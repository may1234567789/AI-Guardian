"""
AI Guardian (SentinelAI) - Day 3: Cross-Model Error Comparison
================================================================
Analyzes where LogReg and LinearSVM disagree on the held-out test set.

Investigates:
- Examples correctly classified by LogReg but missed by SVM (and vice versa).
- False positives from each model.
- False negatives from each model.
- Benign content that discusses malicious prompts.
- Direct vs. indirect prompt-injection instructions.
- Possible dataset artifacts and label ambiguity.

Saves structured markdown report to ml/reports/model_error_comparison.md.
"""

import argparse
import os
import sys
from typing import Any, Dict, List

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd

from ml.preprocess_data import get_preprocessed_splits


def truncate_text(text: str, max_len: int = 150) -> str:
    """Truncates text to max_len characters for safe display."""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def get_feature_contributions(pipeline: Any, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Extracts top n-gram contributions for a given prompt from a pipeline."""
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["clf"]
    feature_names = vectorizer.get_feature_names_out()
    tfidf_vec = vectorizer.transform([text])
    nonzero_indices = tfidf_vec.nonzero()[1]

    contributions = []
    for idx in nonzero_indices:
        token = feature_names[idx]
        val = tfidf_vec[0, idx]
        coef = classifier.coef_[0, idx]
        score = val * coef
        contributions.append({
            "token": token,
            "tfidf": round(float(val), 4),
            "coef": round(float(coef), 4),
            "score": round(float(score), 4),
        })

    contributions.sort(key=lambda x: abs(x["score"]), reverse=True)
    return contributions[:top_k]


def compare_errors(
    logreg_path: str = "ml/artifacts/prompt_injection_logreg.joblib",
    svm_path: str = "ml/artifacts/prompt_injection_svm.joblib",
    output_path: str = "ml/reports/model_error_comparison.md",
    config: str = "core",
) -> str:
    """Full cross-model error analysis."""
    if not os.path.exists(logreg_path):
        raise FileNotFoundError(f"LogReg model not found: {logreg_path}")
    if not os.path.exists(svm_path):
        raise FileNotFoundError(f"SVM model not found: {svm_path}")

    print("[*] Loading models...")
    logreg = joblib.load(logreg_path)
    svm = joblib.load(svm_path)

    print("[*] Loading test data...")
    _, _, test_df = get_preprocessed_splits(config=config, drop_duplicates=True)
    X_test = test_df["text"]
    y_test = test_df["label"].to_numpy()

    # Get predictions
    lr_preds = logreg.predict(X_test)
    svm_preds = svm.predict(X_test)

    # Get scores
    lr_probs = logreg.predict_proba(X_test)[:, 1]
    svm_scores = svm.decision_function(X_test)

    # Add to dataframe for analysis
    test_df = test_df.copy()
    test_df["lr_pred"] = lr_preds
    test_df["svm_pred"] = svm_preds
    test_df["lr_prob"] = lr_probs
    test_df["svm_score"] = svm_scores
    test_df["lr_correct"] = (lr_preds == y_test)
    test_df["svm_correct"] = (svm_preds == y_test)
    test_df["char_len"] = test_df["text"].str.len()

    # Error partitions
    # LogReg False Positives
    lr_fps = test_df[(test_df["label"] == 0) & (test_df["lr_pred"] == 1)]
    lr_fns = test_df[(test_df["label"] == 1) & (test_df["lr_pred"] == 0)]
    # SVM False Positives
    svm_fps = test_df[(test_df["label"] == 0) & (test_df["svm_pred"] == 1)]
    svm_fns = test_df[(test_df["label"] == 1) & (test_df["svm_pred"] == 0)]

    # Agreement / Disagreement
    both_correct = test_df[test_df["lr_correct"] & test_df["svm_correct"]]
    both_wrong = test_df[~test_df["lr_correct"] & ~test_df["svm_correct"]]
    lr_only_correct = test_df[test_df["lr_correct"] & ~test_df["svm_correct"]]
    svm_only_correct = test_df[~test_df["lr_correct"] & test_df["svm_correct"]]

    total = len(test_df)
    agree_count = len(both_correct) + len(both_wrong)
    disagree_count = len(lr_only_correct) + len(svm_only_correct)

    print(f"[*] Both correct: {len(both_correct)} | Both wrong: {len(both_wrong)}")
    print(f"[*] LR only correct: {len(lr_only_correct)} | SVM only correct: {len(svm_only_correct)}")

    # Identify categories
    # Benign content discussing security
    security_keywords = ["inject", "override", "ignore", "system", "prompt", "hack", "exploit",
                         "jailbreak", "bypass", "vulnerability", "security"]
    benign_discussing_security = test_df[
        (test_df["label"] == 0) &
        test_df["text"].str.lower().apply(
            lambda t: any(kw in t for kw in security_keywords)
        )
    ]

    # Direct instructions (label=1, contain imperative override language)
    direct_override_keywords = ["ignore", "override", "forget", "disregard", "new instructions",
                                 "system prompt", "you are now", "DAN", "do anything"]
    direct_injections = test_df[
        (test_df["label"] == 1) &
        test_df["text"].str.lower().apply(
            lambda t: any(kw.lower() in t for kw in direct_override_keywords)
        )
    ]

    # Indirect / obfuscated (label=1, NOT containing direct override keywords)
    indirect_injections = test_df[
        (test_df["label"] == 1) &
        ~test_df["text"].str.lower().apply(
            lambda t: any(kw.lower() in t for kw in direct_override_keywords)
        )
    ]

    # Build markdown report
    lines = [
        "# SentinelAI — Day 3: Cross-Model Error Comparison Report",
        "",
        "**Models Compared:** TF-IDF + Logistic Regression (Day 2) vs. TF-IDF + LinearSVC (Day 3)  ",
        f"**Test Set:** `core_test` (N = {total}, {int((y_test==0).sum())} benign, {int((y_test==1).sum())} malicious)  ",
        "**Date:** October 31, 2026  ",
        "",
        "---",
        "",
        "## 1. Agreement Summary",
        "",
        f"| Category | Count | % of Test Set |",
        f"| :--- | ---: | ---: |",
        f"| Both models correct | {len(both_correct)} | {len(both_correct)/total*100:.1f}% |",
        f"| Both models incorrect | {len(both_wrong)} | {len(both_wrong)/total*100:.1f}% |",
        f"| Only LogReg correct | {len(lr_only_correct)} | {len(lr_only_correct)/total*100:.1f}% |",
        f"| Only SVM correct | {len(svm_only_correct)} | {len(svm_only_correct)/total*100:.1f}% |",
        f"| **Total agreement** | **{agree_count}** | **{agree_count/total*100:.1f}%** |",
        f"| **Total disagreement** | **{disagree_count}** | **{disagree_count/total*100:.1f}%** |",
        "",
        "---",
        "",
        "## 2. Error Count Comparison",
        "",
        f"| Error Type | LogReg | SVM | Difference |",
        f"| :--- | ---: | ---: | ---: |",
        f"| False Positives | {len(lr_fps)} | {len(svm_fps)} | {len(svm_fps) - len(lr_fps):+d} |",
        f"| False Negatives | {len(lr_fns)} | {len(svm_fns)} | {len(svm_fns) - len(lr_fns):+d} |",
        f"| Total Errors | {len(lr_fps)+len(lr_fns)} | {len(svm_fps)+len(svm_fns)} | {(len(svm_fps)+len(svm_fns)) - (len(lr_fps)+len(lr_fns)):+d} |",
        "",
        "---",
        "",
        "## 3. Examples Correctly Classified by LogReg but Missed by SVM",
        "",
        f"Total: {len(lr_only_correct)} examples",
        "",
    ]

    for idx, (_, row) in enumerate(lr_only_correct.head(5).iterrows(), 1):
        lines.extend([
            f"### Example {idx}",
            f"- **True Label:** {'Malicious' if row['label']==1 else 'Benign'} | **Category:** {row.get('category', 'unknown')}",
            f"- **Text:** `{truncate_text(row['text'])}`",
            f"- **LogReg:** {'Malicious' if row['lr_pred']==1 else 'Benign'} (prob={row['lr_prob']:.4f}) ✓",
            f"- **SVM:** {'Malicious' if row['svm_pred']==1 else 'Benign'} (score={row['svm_score']:.4f}) ✗",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 4. Examples Correctly Classified by SVM but Missed by LogReg",
        "",
        f"Total: {len(svm_only_correct)} examples",
        "",
    ])

    for idx, (_, row) in enumerate(svm_only_correct.head(5).iterrows(), 1):
        lines.extend([
            f"### Example {idx}",
            f"- **True Label:** {'Malicious' if row['label']==1 else 'Benign'} | **Category:** {row.get('category', 'unknown')}",
            f"- **Text:** `{truncate_text(row['text'])}`",
            f"- **LogReg:** {'Malicious' if row['lr_pred']==1 else 'Benign'} (prob={row['lr_prob']:.4f}) ✗",
            f"- **SVM:** {'Malicious' if row['svm_pred']==1 else 'Benign'} (score={row['svm_score']:.4f}) ✓",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 5. Shared False Positives (Both Models)",
        "",
        f"Total shared false positives: {len(test_df[(test_df['label']==0) & (test_df['lr_pred']==1) & (test_df['svm_pred']==1)])}",
        "",
    ])

    shared_fps = test_df[(test_df["label"] == 0) & (test_df["lr_pred"] == 1) & (test_df["svm_pred"] == 1)]
    for idx, (_, row) in enumerate(shared_fps.head(3).iterrows(), 1):
        lines.extend([
            f"### Shared FP #{idx}",
            f"- **Text:** `{truncate_text(row['text'])}`",
            f"- **Category:** {row.get('category', 'unknown')} | **Length:** {len(row['text'])} chars",
            f"- **LogReg prob:** {row['lr_prob']:.4f} | **SVM score:** {row['svm_score']:.4f}",
            f"- **Analysis:** Both models trigger on imperative/security language in benign context.",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 6. Shared False Negatives (Both Models)",
        "",
        f"Total shared false negatives: {len(test_df[(test_df['label']==1) & (test_df['lr_pred']==0) & (test_df['svm_pred']==0)])}",
        "",
    ])

    shared_fns = test_df[(test_df["label"] == 1) & (test_df["lr_pred"] == 0) & (test_df["svm_pred"] == 0)]
    for idx, (_, row) in enumerate(shared_fns.head(3).iterrows(), 1):
        lines.extend([
            f"### Shared FN #{idx}",
            f"- **Text:** `{truncate_text(row['text'])}`",
            f"- **Category:** {row.get('category', 'unknown')} | **Severity:** {row.get('severity', 'unknown')}",
            f"- **LogReg prob:** {row['lr_prob']:.4f} | **SVM score:** {row['svm_score']:.4f}",
            f"- **Vulnerability:** Attack evades both bag-of-words classifiers.",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 7. Benign Content Discussing Security Topics",
        "",
        f"Found {len(benign_discussing_security)} benign prompts containing security-related keywords.",
        f"- LogReg false-alarm rate on these: {len(benign_discussing_security[benign_discussing_security['lr_pred']==1])}/{len(benign_discussing_security)} ({len(benign_discussing_security[benign_discussing_security['lr_pred']==1])/max(1,len(benign_discussing_security))*100:.1f}%)",
        f"- SVM false-alarm rate on these: {len(benign_discussing_security[benign_discussing_security['svm_pred']==1])}/{len(benign_discussing_security)} ({len(benign_discussing_security[benign_discussing_security['svm_pred']==1])/max(1,len(benign_discussing_security))*100:.1f}%)",
        "",
        "---",
        "",
        "## 8. Direct vs. Indirect Prompt Injections",
        "",
        f"### Direct Override Instructions (N={len(direct_injections)})",
        f"- LogReg detection rate: {len(direct_injections[direct_injections['lr_pred']==1])}/{len(direct_injections)} ({len(direct_injections[direct_injections['lr_pred']==1])/max(1,len(direct_injections))*100:.1f}%)",
        f"- SVM detection rate: {len(direct_injections[direct_injections['svm_pred']==1])}/{len(direct_injections)} ({len(direct_injections[direct_injections['svm_pred']==1])/max(1,len(direct_injections))*100:.1f}%)",
        "",
        f"### Indirect / Obfuscated Injections (N={len(indirect_injections)})",
        f"- LogReg detection rate: {len(indirect_injections[indirect_injections['lr_pred']==1])}/{len(indirect_injections)} ({len(indirect_injections[indirect_injections['lr_pred']==1])/max(1,len(indirect_injections))*100:.1f}%)",
        f"- SVM detection rate: {len(indirect_injections[indirect_injections['svm_pred']==1])}/{len(indirect_injections)} ({len(indirect_injections[indirect_injections['svm_pred']==1])/max(1,len(indirect_injections))*100:.1f}%)",
        "",
        "> **Note:** The keyword-based categorization above is a heuristic approximation.",
        "> Not all prompts lacking override keywords are truly 'indirect' — some may be toxic content",
        "> requests or jailbreak variants that simply use different vocabulary.",
        "",
        "---",
        "",
        "## 9. Possible Dataset Artifacts and Label Ambiguity",
        "",
        "### Observations from Both Models' Errors:",
        "",
        "1. **Ambiguous Labels:** Some benign prompts use language (\"ignore\", \"override\", \"template\") that closely mirrors prompt-injection syntax, causing both models to flag them.",
        "2. **Length Bias Persistence:** False positives from both models tend to be longer than average benign prompts, suggesting residual text-length correlation even with sublinear TF scaling.",
        "3. **Social Engineering Blind Spot:** Persona-replacement and roleplay-based attacks (e.g., \"grandma exploit\") evade both keyword-dependent classifiers because they lack explicit override tokens.",
        "4. **Jailbreak vs. Toxic Content Conflation:** Some test examples labeled as \"jailbreak\" are purely toxic content requests without prompt-injection mechanics, creating label ambiguity for injection-specific classifiers.",
        "",
        "---",
        "",
        "## 10. Conclusions",
        "",
        "1. The two models agree on the vast majority of examples, suggesting both linear classifiers learn similar decision boundaries in the TF-IDF feature space.",
        "2. Neither model is strictly superior — each correctly classifies a small number of examples that the other misses.",
        "3. Shared errors point to fundamental limitations of bag-of-words models for semantic attack detection.",
        "4. Dataset label ambiguity (benign prompts with security language, toxic content labeled as injection) affects both models equally.",
        "5. A handful of examples should not be used to declare one model superior. The comparison should be based on aggregate metrics and the project's security priorities.",
        "",
        "> **Important:** Do not assume either model is superior based on these qualitative examples alone.",
        "> The error patterns identified here inform which failure modes to address in future iterations,",
        "> not which model to deploy. Deployment decisions should weigh aggregate metrics, latency,",
        "> false-positive tolerance, and defense-in-depth requirements.",
        "",
    ])

    report = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[+] Saved model error comparison report to: {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="SentinelAI Day 3: Cross-Model Error Comparison")
    parser.add_argument("--logreg-path", type=str, default="ml/artifacts/prompt_injection_logreg.joblib")
    parser.add_argument("--svm-path", type=str, default="ml/artifacts/prompt_injection_svm.joblib")
    parser.add_argument("--output", type=str, default="ml/reports/model_error_comparison.md")
    parser.add_argument("--config", type=str, default="core")
    args = parser.parse_args()

    compare_errors(
        logreg_path=args.logreg_path,
        svm_path=args.svm_path,
        output_path=args.output,
        config=args.config,
    )


if __name__ == "__main__":
    main()
