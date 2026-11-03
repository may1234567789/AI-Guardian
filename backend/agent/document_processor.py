from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class DocumentProcessor:
    """Parses untrusted document text without trusting embedded instructions."""

    def __init__(self):
        self._document_cache: Dict[str, str] = {}

    @staticmethod
    def normalize_document(document: Any) -> str:
        if document is None:
            return ""
        if isinstance(document, str):
            return document.strip()
        if isinstance(document, dict):
            if "text" in document:
                return str(document["text"]).strip()
            if "content" in document:
                return str(document["content"]).strip()
            return " ".join(str(value).strip() for value in document.values() if str(value).strip())
        if isinstance(document, Iterable) and not isinstance(document, (bytes, bytearray)):
            return " ".join(str(part).strip() for part in document if str(part).strip())
        return str(document).strip()

    def process(self, document: Any) -> Dict[str, Any]:
        text = self.normalize_document(document)
        if not text:
            return {
                "text": "",
                "word_count": 0,
                "is_untrusted_document": False,
                "instruction_like_sentences": [],
                "trust_level": "untrusted",
            }

        sentences = [sentence.strip() for sentence in text.split(".") if sentence.strip()]
        instruction_like = [sentence for sentence in sentences if any(marker in sentence.lower() for marker in ("ignore previous instructions", "override", "do not follow", "act as", "new instructions", "system prompt", "bypass"))]
        return {
            "text": text,
            "word_count": len(text.split()),
            "is_untrusted_document": True,
            "instruction_like_sentences": instruction_like,
            "trust_level": "untrusted",
        }

    def extract_text(self, document: Any) -> str:
        return self.process(document)["text"]

    def get_document_summary(self, document: Any) -> Dict[str, Any]:
        processed = self.process(document)
        summary = {
            "source": "untrusted_document",
            "trust_level": processed["trust_level"],
            "word_count": processed["word_count"],
            "instruction_like_sentences": processed["instruction_like_sentences"],
        }
        if processed["text"]:
            summary["preview"] = processed["text"][:240]
        return summary


__all__ = ["DocumentProcessor"]
