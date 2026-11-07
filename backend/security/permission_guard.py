"""Permission guard that enforces deterministic authorization and ML risk checks."""

from __future__ import annotations

from typing import Any, Dict

from backend.security.policy_engine import PolicyEngine
from backend.security.prompt_detector import PromptDetector


class PermissionGuard:
    """Policy-first authorization gate that does not allow ML risk to override explicit denials."""

    INJECTION_PATTERNS = (
        "ignore previous instructions",
        "reveal the system prompt",
        "override prior instructions",
        "ignore the instructions",
        "ignore the system prompt",
        "act as if",
        "pretend you are",
        "developer message",
        "bypass policy",
        "jailbreak",
        "new instructions",
        "system prompt",
        "secret prompt",
        "do not follow",
    )

    def __init__(self, policy_engine: PolicyEngine | None = None, prompt_detector: PromptDetector | None = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self.prompt_detector = prompt_detector or PromptDetector()

    @staticmethod
    def _contains_explicit_injection_markers(prompt: str) -> bool:
        lowered = prompt.lower()
        return any(marker in lowered for marker in PermissionGuard.INJECTION_PATTERNS)

    @staticmethod
    def _looks_like_public_safe_request(prompt: str) -> bool:
        lowered = prompt.lower()
        public_terms = (
            "public faq",
            "public knowledge base",
            "onboarding steps",
            "onboarding guide",
            "public onboarding",
            "public documentation",
            "public manual",
            "faq",
            "knowledge base",
            "documentation",
            "release notes",
            "setup instructions",
        )
        return any(term in lowered for term in public_terms)

    def authorize(
        self,
        prompt: str,
        role: str,
        action: str,
        *,
        confirm_delete: bool = False,
    ) -> Dict[str, Any]:
        policy_result = self.policy_engine.evaluate_action(role, action, confirm_delete=confirm_delete)
        if not policy_result["authorized"]:
            return {
                "authorized": False,
                "reason": policy_result["reason"],
                "policy_decision": policy_result,
            }

        try:
            ml_result = self.prompt_detector.detect(prompt)
        except (RuntimeError, OSError, ValueError, TypeError) as exc:
            return {
                "authorized": False,
                "reason": f"Prompt detector unavailable; request blocked closed ({type(exc).__name__}).",
                "policy_decision": policy_result,
                "ml_detection": {
                    "is_suspicious": None,
                    "predicted_label": "unavailable",
                    "risk_score": 1.0,
                    "model_name": "unavailable",
                    "detection_reason": "The prompt detector failed; protected actions require a working detector.",
                },
                "decision": "BLOCK",
            }

        if self._contains_explicit_injection_markers(prompt):
            return {
                "authorized": False,
                "reason": "Prompt contains explicit injection markers; the request was blocked before execution.",
                "policy_decision": policy_result,
                "ml_detection": ml_result,
                "decision": "BLOCK",
            }

        public_safe = action == "search_public_documents" and self._looks_like_public_safe_request(prompt)
        if ml_result.get("is_suspicious") and not public_safe:
            if action in {"update_simulated_record", "send_simulated_email", "delete_simulated_resource"}:
                return {
                    "authorized": False,
                    "reason": "ML detection flagged a suspicious prompt for a guarded action; the action was blocked.",
                    "policy_decision": policy_result,
                    "ml_detection": ml_result,
                    "decision": "BLOCK",
                }
            return {
                "authorized": False,
                "reason": "ML detection flagged a suspicious prompt for a protected action; review is required before execution.",
                "policy_decision": policy_result,
                "ml_detection": ml_result,
                "decision": "REVIEW",
            }

        return {
            "authorized": True,
            "reason": "Authorization granted by policy and accepted ML context.",
            "policy_decision": policy_result,
            "ml_detection": ml_result,
            "decision": "ALLOW",
        }
