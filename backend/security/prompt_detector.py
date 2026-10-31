"""Prompt injection detector built on the best verified Day 3 model artifact."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Union

import joblib
import numpy as np


class PromptDetector:
    """Loads the best verified trained model and classifies suspicious prompts."""

    def __init__(
        self,
        model_path: str | None = None,
        threshold: float | None = None,
    ):
        self.project_root = Path(__file__).resolve().parents[2]
        self.default_model_path = self._resolve_default_model()
        self.model_path = Path(model_path) if model_path else self.default_model_path
        self.threshold = threshold
        self._model = None
        self._metadata = self._load_metadata()
        self._load_model()

    def _resolve_default_model(self) -> Path:
        preferred = self.project_root / "ml" / "artifacts" / "prompt_injection_svm.joblib"
        if preferred.exists():
            return preferred
        logistic = self.project_root / "ml" / "artifacts" / "prompt_injection_logreg.joblib"
        if logistic.exists():
            return logistic
        raise FileNotFoundError("No trained prompt-injection model artifacts were found in ml/artifacts/.")

    def _load_metadata(self) -> dict:
        metadata_candidates = [
            self.project_root / "ml" / "artifacts" / "svm_model_metadata.json",
            self.project_root / "ml" / "artifacts" / "model_metadata.json",
        ]
        for metadata_path in metadata_candidates:
            if metadata_path.exists():
                with metadata_path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
        return {}

    def _load_model(self):
        try:
            self._model = joblib.load(self.model_path)
        except (FileNotFoundError, OSError, ValueError, EOFError) as exc:
            raise RuntimeError(f"Unable to load prompt-injection model from '{self.model_path}'.") from exc

        if hasattr(self._model, "classes_"):
            self.malicious_label = self._model.classes_[1] if len(self._model.classes_) > 1 else self._model.classes_[0]
        else:
            self.malicious_label = 1

        self.model_name = getattr(self._model, "__class__", type(self._model)).__name__

        if self.threshold is None:
            if "prompt_injection_svm" in self.model_path.name:
                self.threshold = 0.03
            else:
                self.threshold = 0.71

    @staticmethod
    def _normalize_texts(inputs: Union[str, Sequence[str], Iterable[str]]) -> List[str]:
        if isinstance(inputs, str):
            texts = [inputs]
        else:
            try:
                texts = list(inputs)
            except TypeError as exc:
                raise ValueError("Input must be a string or an iterable of strings.") from exc

        normalized: List[str] = []
        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise ValueError(f"Input at position {index} must be a string.")
            trimmed = text.strip()
            if trimmed == "":
                raise ValueError(f"Input at position {index} is empty after trimming.")
            if len(trimmed) > 20000:
                raise ValueError(f"Input at position {index} exceeds the maximum supported length of 20,000 characters.")
            normalized.append(trimmed)
        return normalized

    def _get_model_features(self, texts: List[str]):
        if not hasattr(self._model, "predict_proba"):
            decision_scores = self._model.decision_function(texts)
            return decision_scores.tolist(), "decision_function"
        probs = self._model.predict_proba(texts)
        malicious_index = np.where(self._model.classes_ == self.malicious_label)[0][0]
        return probs[:, malicious_index].tolist(), "predict_proba"

    def detect(self, text: Union[str, Sequence[str], Iterable[str]]) -> dict:
        texts = self._normalize_texts(text)
        scores, method = self._get_model_features(texts)

        results = []
        for raw_text, score in zip(texts, scores):
            if method == "decision_function":
                predicted_label = "prompt_injection" if score >= self.threshold else "benign"
                suspicious = score >= self.threshold
                risk_score = float(score)
                reason = (
                    "Malicious score exceeds the Day 3 validation-selected decision threshold "
                    f"({self.threshold:.4f}) for the Linear SVM model."
                    if suspicious
                    else "Score is below the Day 3 validation-selected decision threshold; no malicious classification was triggered."
                )
            else:
                probability = float(score)
                predicted_label = "prompt_injection" if probability >= self.threshold else "benign"
                suspicious = probability >= self.threshold
                risk_score = probability
                reason = (
                    f"ML probability score {probability:.4f} exceeds the validated threshold {self.threshold:.4f}."
                    if suspicious
                    else f"ML probability score {probability:.4f} is below the validated threshold {self.threshold:.4f}."
                )

            result = {
                "is_suspicious": suspicious,
                "predicted_label": predicted_label,
                "risk_score": round(risk_score, 6),
                "model_name": self.model_path.name,
                "detection_reason": reason,
            }
            results.append(result)

        return results[0] if len(results) == 1 else results

    def detect_batch(self, texts: Iterable[str]) -> List[dict]:
        values = list(texts)
        if not values:
            return []
        if isinstance(values[0], str):
            return [self.detect(text) for text in values]
        raise ValueError("detect_batch expects an iterable of strings.")

    def summarize_model(self) -> dict:
        return {
            "model_path": str(self.model_path),
            "metadata": self._metadata,
            "threshold": self.threshold,
            "malicious_label": "prompt_injection",
        }
