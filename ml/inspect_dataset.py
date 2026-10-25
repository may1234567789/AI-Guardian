"""
AI Guardian (SentinelAI) - Day 1: Dataset Inspection Script
============================================================
Safely inspects the Hugging Face Prompt Injection dataset:
`cyberec/Prompt-injection-dataset`

Evaluates schema, splits, label distributions, text lengths, missing values,
duplicates, group leakage, and potential data quality anomalies.

Security Note: All dataset text is treated as untrusted data. Strings are never
evaluated, executed, or passed to dynamic execution engines.
"""

import argparse
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

import datasets
import numpy as np
import pandas as pd


DATASET_NAME = "cyberec/Prompt-injection-dataset"
SUPPORTED_CONFIGS = ["core", "full"]


def load_hf_dataset(config_name: str = "core") -> datasets.DatasetDict:
    """
    Safely load the specified configuration from Hugging Face datasets.
    """
    if config_name not in SUPPORTED_CONFIGS:
        raise ValueError(
            f"Unsupported config: {config_name}. Expected one of {SUPPORTED_CONFIGS}"
        )
    print(f"[*] Loading dataset '{DATASET_NAME}' with configuration '{config_name}'...")
    ds = datasets.load_dataset(DATASET_NAME, config_name)
    return ds


def inspect_split(split_name: str, dataset_split: datasets.Dataset) -> Dict[str, Any]:
    """
    Inspect a single dataset split and return computed quality metrics.
    """
    df = dataset_split.to_pandas()
    num_rows = len(df)

    # Missing / Null values
    null_counts = df.isnull().sum().to_dict()

    # Empty / whitespace-only text
    empty_text_count = 0
    whitespace_text_count = 0
    if "text" in df.columns:
        text_series = df["text"].astype(str)
        empty_text_count = int((text_series == "").sum())
        whitespace_text_count = int((text_series.str.strip() == "").sum())

    # Duplicates within split (convert list/array columns to tuples for hashing)
    hashable_cols = {}
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, np.ndarray))).any():
            hashable_cols[col] = df[col].apply(lambda x: tuple(x) if isinstance(x, (list, np.ndarray)) else x)
        else:
            hashable_cols[col] = df[col]
    df_hashable = pd.DataFrame(hashable_cols)

    exact_row_duplicates = int(df_hashable.duplicated().sum())
    exact_text_duplicates = (
        int(df["text"].astype(str).duplicated().sum()) if "text" in df.columns else 0
    )

    # Label distribution
    label_distribution = {}
    if "label" in df.columns:
        counts = df["label"].value_counts(dropna=False).to_dict()
        label_distribution = {
            str(k): {"count": int(v), "percentage": round(float(v) / num_rows * 100, 2)}
            for k, v in counts.items()
        }

    # Text length statistics (character and word counts)
    char_stats = {}
    word_stats = {}
    if "text" in df.columns:
        char_lens = df["text"].astype(str).str.len()
        word_lens = df["text"].astype(str).str.split().str.len()

        char_stats = {
            "min": int(char_lens.min()),
            "max": int(char_lens.max()),
            "mean": round(float(char_lens.mean()), 2),
            "median": float(char_lens.median()),
            "std": round(float(char_lens.std()), 2),
            "p25": float(np.percentile(char_lens, 25)),
            "p75": float(np.percentile(char_lens, 75)),
            "p95": float(np.percentile(char_lens, 95)),
            "p99": float(np.percentile(char_lens, 99)),
        }

        word_stats = {
            "min": int(word_lens.min()),
            "max": int(word_lens.max()),
            "mean": round(float(word_lens.mean()), 2),
            "median": float(word_lens.median()),
            "p95": float(np.percentile(word_lens, 95)),
            "p99": float(np.percentile(word_lens, 99)),
        }

    # Category distribution if available
    category_distribution = {}
    if "category" in df.columns:
        category_counts = df["category"].value_counts().head(10).to_dict()
        category_distribution = {str(k): int(v) for k, v in category_counts.items()}

    # Severity distribution if available
    severity_distribution = {}
    if "severity" in df.columns:
        sev_counts = df["severity"].value_counts(dropna=False).to_dict()
        severity_distribution = {str(k): int(v) for k, v in sev_counts.items()}

    # Augmented flags if available
    augmented_counts = {}
    if "augmented" in df.columns:
        aug_counts = df["augmented"].value_counts(dropna=False).to_dict()
        augmented_counts = {str(k): int(v) for k, v in aug_counts.items()}

    return {
        "split_name": split_name,
        "num_rows": num_rows,
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": null_counts,
        "empty_text_count": empty_text_count,
        "whitespace_text_count": whitespace_text_count,
        "exact_row_duplicates": exact_row_duplicates,
        "exact_text_duplicates": exact_text_duplicates,
        "label_distribution": label_distribution,
        "char_stats": char_stats,
        "word_stats": word_stats,
        "category_top10": category_distribution,
        "severity_distribution": severity_distribution,
        "augmented_counts": augmented_counts,
    }


def check_cross_split_leakage(ds: datasets.DatasetDict) -> Dict[str, Any]:
    """
    Check for data leakage across splits:
    1. Exact text overlap between train, validation, and test.
    2. Group ID overlap between train, validation, and test.
    """
    split_names = list(ds.keys())
    split_dfs = {s: ds[s].to_pandas() for s in split_names}

    text_overlap_results = {}
    group_overlap_results = {}

    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]
            pair_name = f"{s1}_vs_{s2}"

            # Text overlap
            texts_1 = set(split_dfs[s1]["text"].astype(str).str.strip())
            texts_2 = set(split_dfs[s2]["text"].astype(str).str.strip())
            common_texts = texts_1.intersection(texts_2)
            text_overlap_results[pair_name] = {
                "overlap_count": len(common_texts),
                "overlap_percentage_s1": round(len(common_texts) / len(texts_1) * 100, 3) if texts_1 else 0.0,
                "overlap_percentage_s2": round(len(common_texts) / len(texts_2) * 100, 3) if texts_2 else 0.0,
            }

            # Group ID overlap (if group_id exists)
            if "group_id" in split_dfs[s1].columns and "group_id" in split_dfs[s2].columns:
                groups_1 = set(split_dfs[s1]["group_id"].dropna().astype(str))
                groups_2 = set(split_dfs[s2]["group_id"].dropna().astype(str))
                common_groups = groups_1.intersection(groups_2)
                group_overlap_results[pair_name] = {
                    "overlap_count": len(common_groups),
                    "common_groups_sample": list(common_groups)[:5],
                }

    return {
        "text_overlaps": text_overlap_results,
        "group_overlaps": group_overlap_results,
    }


def find_representative_examples(
    dataset_split: datasets.Dataset, num_examples: int = 3
) -> List[Dict[str, Any]]:
    """
    Safely extract representative examples from malicious (label 1) and benign (label 0) classes.
    Text is safely sanitized to avoid markdown rendering issues or raw control characters.
    """
    df = dataset_split.to_pandas()
    examples = []

    for label_val in sorted(df["label"].unique()):
        subset = df[df["label"] == label_val]
        sample_rows = subset.head(num_examples)
        for _, row in sample_rows.iterrows():
            # Sanitize text representation safely
            raw_text = str(row["text"])
            safe_text = raw_text.replace("\r", " ").replace("\n", " ").strip()
            if len(safe_text) > 140:
                safe_text = safe_text[:137] + "..."

            examples.append({
                "label": int(row["label"]),
                "category": str(row.get("category", "N/A")),
                "severity": str(row.get("severity", "N/A")),
                "source": str(row.get("source", "N/A")),
                "group_id": str(row.get("group_id", "N/A")),
                "augmented": bool(row.get("augmented", False)),
                "text_snippet": safe_text,
                "full_char_len": len(raw_text),
            })
    return examples


def run_inspection(config_name: str = "core", save_local: bool = True, data_dir: str = "ml/data") -> Dict[str, Any]:
    """
    Main programmatic entry point for dataset inspection.
    """
    ds = load_hf_dataset(config_name)

    inspection_report = {
        "dataset_name": DATASET_NAME,
        "config_name": config_name,
        "available_splits": list(ds.keys()),
        "split_reports": {},
        "leakage_analysis": check_cross_split_leakage(ds),
        "representative_examples": {},
    }

    print("\n" + "=" * 70)
    print(f" DATASET INSPECTION REPORT: {DATASET_NAME} (Config: {config_name})")
    print("=" * 70)

    for split_name in ds.keys():
        print(f"\n--- Split: {split_name} ({len(ds[split_name])} examples) ---")
        rep = inspect_split(split_name, ds[split_name])
        inspection_report["split_reports"][split_name] = rep

        print(f"Columns: {rep['columns']}")
        print(f"Null values: {rep['null_counts']}")
        print(f"Exact text duplicates in split: {rep['exact_text_duplicates']}")
        print(f"Empty/whitespace texts: {rep['whitespace_text_count']}")
        print("Label distribution:")
        for lbl, stats in rep["label_distribution"].items():
            print(f"  Class {lbl}: {stats['count']} ({stats['percentage']}%)")

        print("Text character length summary:")
        cs = rep["char_stats"]
        print(f"  Min: {cs['min']}, Median: {cs['median']}, Mean: {cs['mean']}, Max: {cs['max']}, P95: {cs['p95']}, P99: {cs['p99']}")

        # Save local copies if requested
        if save_local:
            os.makedirs(data_dir, exist_ok=True)
            parquet_path = os.path.join(data_dir, f"{config_name}_{split_name}.parquet")
            csv_path = os.path.join(data_dir, f"{config_name}_{split_name}.csv")
            df = ds[split_name].to_pandas()
            df.to_parquet(parquet_path, index=False)
            df.to_csv(csv_path, index=False)
            print(f"  -> Saved local copy to {parquet_path} and {csv_path}")

        # Extract representative examples
        inspection_report["representative_examples"][split_name] = find_representative_examples(ds[split_name])

    # Print leakage analysis
    print("\n" + "=" * 70)
    print(" CROSS-SPLIT DATA LEAKAGE & INTEGRITY CHECK")
    print("=" * 70)
    leakage = inspection_report["leakage_analysis"]
    for pair, stats in leakage["text_overlaps"].items():
        print(f"Text overlap [{pair}]: {stats['overlap_count']} identical prompts")
    for pair, stats in leakage["group_overlaps"].items():
        print(f"Group ID overlap [{pair}]: {stats['overlap_count']} common group IDs")

    return inspection_report


def main():
    parser = argparse.ArgumentParser(description="Inspect Prompt Injection Dataset for AI Guardian")
    parser.add_argument(
        "--config",
        choices=SUPPORTED_CONFIGS,
        default="core",
        help="Dataset configuration to inspect ('core' or 'full')",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save local Parquet/CSV files",
    )
    parser.add_argument(
        "--data-dir",
        default="ml/data",
        help="Target directory for saving local data copies",
    )
    args = parser.parse_args()

    run_inspection(config_name=args.config, save_local=not args.no_save, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
