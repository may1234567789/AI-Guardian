"""Deterministic detection of sensitive data in text input."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence


class DataLeakDetector:
    """Safely detects common sensitive data patterns without exposing full secrets."""

    DEFAULT_CONFIDENTIAL_KEYWORDS = (
        "api key",
        "secret",
        "token",
        "password",
        "private key",
        "customer id",
        "ssn",
        "oauth",
        "access key",
    )

    def __init__(self, confidential_phrases: Sequence[str] | None = None):
        self.confidential_phrases = tuple((confidential_phrases or self.DEFAULT_CONFIDENTIAL_KEYWORDS))
        self._patterns = {
            "EMAIL": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
            "PHONE": re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}"),
            "API_KEY": re.compile(r"(?i)(?:api[_-]?key|token|secret|password|access[_-]?key)[\s:=\"']+([A-Za-z0-9_\-]{12,})"),
            "FINANCIAL_ID": re.compile(r"(?i)(?:account|acct|routing|iban|payment)[\s:#-]*([A-Za-z0-9]{6,20})"),
            "CONFIDENTIAL_KEYWORD": re.compile(r"(?i)" + "|".join(re.escape(p) for p in self.confidential_phrases if p)),
        }

    @staticmethod
    def _mask_email(value: str) -> str:
        local, domain = value.split("@", 1)
        visible = local[:2] if len(local) > 2 else local[:1]
        return f"{visible}***@{domain}"

    @staticmethod
    def _mask_phone(value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 4:
            return "***"
        return f"***-***-{digits[-4:]}"

    @staticmethod
    def _mask_token(value: str) -> str:
        if len(value) <= 6:
            return "***"
        return f"{value[:2]}***{value[-2:]}"

    @staticmethod
    def _mask_financial(value: str) -> str:
        raw = value.strip()
        if len(raw) <= 4:
            return "***"
        return f"{raw[:2]}***{raw[-2:]}"

    @staticmethod
    def _mask_keyword(value: str) -> str:
        return value[:2].upper() + "***"

    def detect(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str):
            raise TypeError("Input text must be a string.")

        findings: List[Dict[str, Any]] = []
        finding_map: Dict[str, Dict[str, Any]] = {}

        for kind, pattern in self._patterns.items():
            matches = pattern.findall(text)
            if kind == "EMAIL":
                for match in sorted(set(matches)):
                    key = kind
                    entry = finding_map.setdefault(key, {"type": kind, "count": 0, "redacted_example": self._mask_email(match)})
                    entry["count"] += 1
            elif kind == "PHONE":
                for match in sorted(set(pattern.findall(text))):
                    value = match.strip()
                    key = kind
                    entry = finding_map.setdefault(key, {"type": kind, "count": 0, "redacted_example": self._mask_phone(value)})
                    entry["count"] += 1
            elif kind in {"API_KEY", "FINANCIAL_ID"}:
                for match in matches:
                    value = str(match).strip()
                    if len(value) < 4:
                        continue
                    key = kind
                    entry = finding_map.setdefault(key, {"type": kind, "count": 0, "redacted_example": self._mask_token(value)})
                    entry["count"] += 1
            elif kind == "CONFIDENTIAL_KEYWORD":
                for keyword in self.confidential_phrases:
                    if re.search(re.escape(keyword), text, flags=re.IGNORECASE):
                        entry = finding_map.setdefault(kind, {"type": "CONFIDENTIAL_KEYWORD", "count": 0, "redacted_example": self._mask_keyword(keyword)})
                        entry["count"] += 1

        for entry in finding_map.values():
            findings.append(entry)

        findings.sort(key=lambda item: item["type"])
        has_sensitive_data = bool(findings)
        risk_score = min(1.0, sum(int(item["count"]) for item in findings) / 5.0)

        return {
            "has_sensitive_data": has_sensitive_data,
            "findings": findings,
            "risk_score": round(risk_score, 4),
        }

    def detect_batch(self, texts: Iterable[str]) -> List[Dict[str, Any]]:
        return [self.detect(text) for text in texts]
