"""
AI Guardian (SentinelAI) - Preprocessing and Data Pipeline
===========================================================
Modular, leakage-safe data preprocessing pipeline for prompt-injection detection.

Key Principles:
- Preserves instruction wording, syntax, and punctuation.
- Avoids aggressive stop-word removal (which would strip crucial security tokens like 'ignore', 'system', 'instructions').
- Validates data types, missing values, empty strings, and label consistency.
- Enforces strict cross-split isolation to prevent data leakage.
"""

import argparse
import os
import sys
from typing import Any, Dict, Optional, Tuple

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd


LABEL_MAPPING = {
    0: "benign",
    1: "prompt_injection",
}


def validate_text_inputs(texts: Any) -> list[str]:
    """Reject invalid pipeline inputs explicitly without coercing them to text."""
    if isinstance(texts, (str, bytes)):
        raise ValueError("Model input must be an iterable of text strings, not a single string.")
    try:
        text_list = list(texts)
    except TypeError as error:
        raise ValueError("Model input must be an iterable of text strings.") from error

    for index, text in enumerate(text_list):
        if not isinstance(text, str):
            raise ValueError(
                f"Model input at position {index} must be a string; "
                f"received {type(text).__name__}."
            )
    return text_list


def clean_text(text: Any) -> str:
    """
    Safely clean and normalize input prompt text without removing critical security tokens.
    
    Preserves:
    - Punctuation (delimiters, brackets, quotes used in injections).
    - Casing / formatting structure.
    - Command keywords ('ignore', 'system', 'override', 'eval').
    """
    if text is None or pd.isna(text):
        return ""
    if not isinstance(text, str):
        text = str(text)
    # Strip extraneous leading/trailing whitespace
    return text.strip()


def validate_split(
    df: pd.DataFrame,
    split_name: str = "dataset",
    text_col: str = "text",
    label_col: str = "label",
) -> Dict[str, Any]:
    """
    Validates a dataset split for nulls, empty strings, valid labels, and duplicates.
    """
    if text_col not in df.columns:
        raise ValueError(f"Split '{split_name}' missing text column '{text_col}'.")
    if label_col not in df.columns:
        raise ValueError(f"Split '{split_name}' missing label column '{label_col}'.")

    total_rows = len(df)
    null_texts = int(df[text_col].isnull().sum())
    null_labels = int(df[label_col].isnull().sum())

    cleaned_texts = df[text_col].apply(clean_text)
    empty_texts = int((cleaned_texts == "").sum())

    # Check labels are exclusively in {0, 1}
    unique_labels = set(df[label_col].unique())
    invalid_labels = unique_labels - {0, 1}
    if invalid_labels:
        raise ValueError(
            f"Split '{split_name}' contains invalid labels: {invalid_labels}. Expected {{0, 1}}."
        )

    exact_duplicates = int(df[text_col].duplicated().sum())
    class_counts = df[label_col].value_counts().to_dict()

    return {
        "split_name": split_name,
        "total_rows": total_rows,
        "null_texts": null_texts,
        "null_labels": null_labels,
        "empty_texts": empty_texts,
        "exact_duplicates": exact_duplicates,
        "class_counts": {int(k): int(v) for k, v in class_counts.items()},
        "is_valid": (
            null_texts == 0
            and null_labels == 0
            and empty_texts == 0
            and len(invalid_labels) == 0
        ),
    }


def preprocess_dataframe(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    text_col: str = "text",
    label_col: str = "label",
    split_name: str = "split",
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Cleans and pre-processes a single split dataframe.
    
    Returns:
        (preprocessed_df, audit_log)
    """
    initial_count = len(df)
    audit = {
        "initial_count": initial_count,
        "null_texts_dropped": 0,
        "null_labels_dropped": 0,
        "empty_texts_dropped": 0,
        "duplicates_dropped": 0,
        "final_count": 0,
    }

    # Shallow copy to avoid mutating original
    df_clean = df.copy()

    # Drop null texts or labels
    null_text_mask = df_clean[text_col].isnull()
    null_label_mask = df_clean[label_col].isnull()
    audit["null_texts_dropped"] = int(null_text_mask.sum())
    audit["null_labels_dropped"] = int(null_label_mask.sum())

    df_clean = df_clean[~null_text_mask & ~null_label_mask]

    # Clean text
    df_clean[text_col] = df_clean[text_col].apply(clean_text)

    # Drop empty or whitespace-only texts
    empty_mask = df_clean[text_col] == ""
    audit["empty_texts_dropped"] = int(empty_mask.sum())
    df_clean = df_clean[~empty_mask]

    # Normalize labels to int
    df_clean[label_col] = df_clean[label_col].astype(int)

    # Handle duplicates if specified
    if drop_duplicates:
        dup_mask = df_clean[text_col].duplicated(keep="first")
        audit["duplicates_dropped"] = int(dup_mask.sum())
        df_clean = df_clean[~dup_mask]

    df_clean = df_clean.reset_index(drop=True)
    audit["final_count"] = len(df_clean)

    return df_clean, audit


def load_split_data(
    split: str,
    config: str = "core",
    data_dir: str = "ml/data",
) -> pd.DataFrame:
    """
    Loads a dataset partition from local Parquet or CSV.
    """
    parquet_path = os.path.join(data_dir, f"{config}_{split}.parquet")
    csv_path = os.path.join(data_dir, f"{config}_{split}.csv")

    if os.path.exists(parquet_path):
        return pd.read_parquet(parquet_path)
    elif os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            f"Dataset split '{split}' not found at '{parquet_path}' or '{csv_path}'."
        )


def check_leakage_across_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    text_col: str = "text",
) -> Dict[str, int]:
    """
    Verifies that no text examples appear across multiple data splits.
    """
    train_texts = set(train_df[text_col])
    val_texts = set(val_df[text_col])
    test_texts = set(test_df[text_col])

    train_val_overlap = len(train_texts.intersection(val_texts))
    train_test_overlap = len(train_texts.intersection(test_texts))
    val_test_overlap = len(val_texts.intersection(test_texts))

    return {
        "train_val_overlap": train_val_overlap,
        "train_test_overlap": train_test_overlap,
        "val_test_overlap": val_test_overlap,
    }


def get_preprocessed_splits(
    config: str = "core",
    data_dir: str = "ml/data",
    drop_duplicates: bool = True,
    text_col: str = "text",
    label_col: str = "label",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads and pre-processes all three official splits (train, validation, test).
    Verifies leakage-safe separation.
    """
    train_raw = load_split_data("train", config, data_dir)
    val_raw = load_split_data("validation", config, data_dir)
    test_raw = load_split_data("test", config, data_dir)

    train_clean, train_audit = preprocess_dataframe(
        train_raw, drop_duplicates, text_col, label_col, "train"
    )
    val_clean, val_audit = preprocess_dataframe(
        val_raw, drop_duplicates, text_col, label_col, "validation"
    )
    test_clean, test_audit = preprocess_dataframe(
        test_raw, drop_duplicates, text_col, label_col, "test"
    )

    leakage = check_leakage_across_splits(train_clean, val_clean, test_clean, text_col)
    if any(count > 0 for count in leakage.values()):
        print(f"[!] Warning: Text leakage detected across splits: {leakage}", file=sys.stderr)

    return train_clean, val_clean, test_clean


def main():
    parser = argparse.ArgumentParser(description="Preprocess SentinelAI Dataset Splits")
    parser.add_argument("--config", type=str, default="core", choices=["core", "full"])
    parser.add_argument("--data-dir", type=str, default="ml/data")
    parser.add_argument("--no-drop-duplicates", action="store_true", help="Retain exact duplicate texts")
    args = parser.parse_args()

    drop_duplicates = not args.no_drop_duplicates

    print("=" * 70)
    print(" SentinelAI - Data Preprocessing & Validation Pipeline")
    print(f" Target Configuration: {args.config} | Data Directory: {args.data_dir}")
    print("=" * 70)

    train_df, val_df, test_df = get_preprocessed_splits(
        config=args.config,
        data_dir=args.data_dir,
        drop_duplicates=drop_duplicates,
    )

    splits = [("Train", train_df), ("Validation", val_df), ("Test", test_df)]

    print("\n--- Split Integrity & Validation Summary ---")
    for name, df in splits:
        validation = validate_split(df, split_name=name)
        c0 = validation["class_counts"].get(0, 0)
        c1 = validation["class_counts"].get(1, 0)
        total = validation["total_rows"]
        pct1 = (c1 / total * 100) if total > 0 else 0
        print(f"[{name.upper()}] Rows: {total:,} | Benign (0): {c0:,} | Malicious (1): {c1:,} ({pct1:.1f}%) | Valid: {validation['is_valid']}")

    leakage = check_leakage_across_splits(train_df, val_df, test_df)
    print("\n--- Cross-Split Leakage Check ---")
    print(f" Train vs. Validation exact text overlap: {leakage['train_val_overlap']}")
    print(f" Train vs. Test exact text overlap:       {leakage['train_test_overlap']}")
    print(f" Validation vs. Test exact text overlap:  {leakage['val_test_overlap']}")

    if sum(leakage.values()) == 0:
        print("[+] SUCCESS: Strict zero-leakage verified across all splits.")
    else:
        print("[!] ALERT: Cross-split overlap detected!")

    print("\n[+] Preprocessing verification complete.")


if __name__ == "__main__":
    main()
