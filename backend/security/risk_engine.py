"""Security risk evaluation that combines ML detection, leak detection, and policy decisions."""

from __future__ import annotations

from typing import Any, Dict

from backend.security.data_leak_detector import DataLeakDetector
from backend.security.permission_guard import PermissionGuard
from backend.security.policy_engine import PolicyEngine
from backend.security.prompt_detector import PromptDetector


class RiskEngine:
    """Coordinates ML risk, data leakage risk, and deterministic authorization checks."""

    def __init__(
        self,
        prompt_detector: PromptDetector | None = None,
        leak_detector: DataLeakDetector | None = None,
        policy_engine: PolicyEngine | None = None,
    ):
        self.prompt_detector = prompt_detector or PromptDetector()
        self.leak_detector = leak_detector or DataLeakDetector()
        self.policy_engine = policy_engine or PolicyEngine()
        self.permission_guard = PermissionGuard(policy_engine=self.policy_engine)

    def evaluate(
        self,
        prompt: str,
        role: str,
        action: str,
        *,
        confirm_delete: bool = False,
        allow_ml_override: bool = False,
    ) -> Dict[str, Any]:
        policy_result = self.policy_engine.evaluate_action(role, action, confirm_delete=confirm_delete)
        ml_result = self._safe_ml_result(prompt)
        leak_result = self.leak_detector.detect(prompt)

        ml_risk = float(ml_result.get("risk_score") or 0.0)
        leak_risk = float(leak_result.get("risk_score", 0.0))

        allowed_by_policy = bool(policy_result.get("authorized", False))
        model_unavailable = ml_result.get("predicted_label") == "unavailable"
        suspicious_prompt = bool(ml_result.get("is_suspicious", False))
        has_sensitive_data = bool(leak_result.get("has_sensitive_data", False))

        if not allowed_by_policy:
            final_authorized = False
            final_reason = policy_result.get("reason", "Denied by deterministic policy.")
        elif model_unavailable:
            final_authorized = False
            final_reason = "Prompt detector is unavailable; the protected action was blocked closed."
        elif suspicious_prompt and not allow_ml_override and action in {"update_simulated_record", "send_simulated_email", "delete_simulated_resource"}:
            final_authorized = False
            final_reason = "Prompt injection detection is suspicious for a sensitive action, so the action was blocked."
        elif has_sensitive_data and leak_risk >= 0.75 and action in {"read_customer_record", "send_simulated_email"}:
            final_authorized = False
            final_reason = "Detected sensitive text in the prompt; action is denied pending redaction and review."
        else:
            final_authorized = True
            final_reason = "Authorized by policy and accepted risk checks."

        return {
            "authorized": final_authorized,
            "role": role,
            "action": action,
            "policy_decision": policy_result,
            "ml_detection": ml_result,
            "data_leak_detection": leak_result,
            "overall_risk_score": round(min(1.0, max(ml_risk, leak_risk)), 4),
            "reason": final_reason,
        }

    def _safe_ml_result(self, prompt: str) -> Dict[str, Any]:
        try:
            return self.prompt_detector.detect(prompt)
        except (RuntimeError, OSError, ValueError, TypeError) as exc:
            return {
                "is_suspicious": None,
                "predicted_label": "unavailable",
                "risk_score": 1.0,
                "model_name": "unavailable",
                "detection_reason": f"Prompt injection model failed ({type(exc).__name__}); protected actions fail closed.",
            }

    def authorize(self, prompt: str, role: str, action: str, *, confirm_delete: bool = False) -> Dict[str, Any]:
        return self.evaluate(prompt, role, action, confirm_delete=confirm_delete)

    def guard(self, prompt: str, role: str, action: str, *, confirm_delete: bool = False) -> Dict[str, Any]:
        return self.permission_guard.authorize(prompt, role, action, confirm_delete=confirm_delete)
