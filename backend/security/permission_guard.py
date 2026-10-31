"""Permission guard that enforces deterministic authorization and ML risk checks."""

from __future__ import annotations

from typing import Any, Dict

from backend.security.policy_engine import PolicyEngine
from backend.security.prompt_detector import PromptDetector


class PermissionGuard:
    """Policy-first authorization gate that does not allow ML risk to override explicit denials."""

    def __init__(self, policy_engine: PolicyEngine | None = None, prompt_detector: PromptDetector | None = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self.prompt_detector = prompt_detector or PromptDetector()

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
        except Exception:
            ml_result = {
                "is_suspicious": False,
                "predicted_label": "unknown",
                "risk_score": 0.0,
                "model_name": "unavailable",
                "detection_reason": "ML model unavailable; policy remains the primary gate.",
            }

        if ml_result.get("is_suspicious") and action in {"update_simulated_record", "send_simulated_email", "delete_simulated_resource"}:
            return {
                "authorized": False,
                "reason": "ML detection flagged a suspicious prompt for a high-impact action; the action was blocked.",
                "policy_decision": policy_result,
                "ml_detection": ml_result,
            }

        return {
            "authorized": True,
            "reason": "Authorization granted by policy and accepted ML context.",
            "policy_decision": policy_result,
            "ml_detection": ml_result,
        }
