from __future__ import annotations

import uuid
from typing import Any, Dict, List

from backend.security.data_leak_detector import DataLeakDetector
from backend.security.policy_engine import PolicyEngine
from backend.security.prompt_detector import PromptDetector
from backend.security.risk_engine import RiskEngine


class SecurityService:
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

    def __init__(self):
        self.prompt_detector = PromptDetector()
        self.data_leak_detector = DataLeakDetector()
        self.policy_engine = PolicyEngine()
        self.risk_engine = RiskEngine(
            prompt_detector=self.prompt_detector,
            leak_detector=self.data_leak_detector,
            policy_engine=self.policy_engine,
        )

    @staticmethod
    def generate_request_id() -> str:
        return f"req-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _contains_explicit_injection_markers(prompt: str) -> bool:
        lowered = prompt.lower()
        return any(marker in lowered for marker in SecurityService.INJECTION_PATTERNS)

    @staticmethod
    def _contains_sensitive_resource_context(prompt: str) -> bool:
        lowered = prompt.lower()
        return any(term in lowered for term in ("private customer", "customer profile", "private record", "secret system", "confidential"))

    @staticmethod
    def _looks_like_public_safe_request(prompt: str, proposed_action: str) -> bool:
        lowered = prompt.lower()
        if proposed_action != "search_public_documents":
            return False
        public_terms = (
            "public faq",
            "public knowledge base",
            "onboarding steps",
            "public documentation",
            "faq",
            "knowledge base",
        )
        if any(term in lowered for term in public_terms):
            return True
        return False

    def scan_prompt(self, prompt: str) -> Dict[str, Any]:
        prompt_analysis = self.prompt_detector.detect(prompt)
        data_leak_analysis = self.data_leak_detector.detect(prompt)
        explicit_injection = self._contains_explicit_injection_markers(prompt)
        sensitive_context = self._contains_sensitive_resource_context(prompt)

        reasons: List[str] = []
        if explicit_injection:
            reasons.append("Prompt injection signals detected.")
        if data_leak_analysis.get("has_sensitive_data"):
            reasons.append("Sensitive data patterns detected in the content.")
        if sensitive_context:
            reasons.append("Request references protected customer resources or confidential content.")
        if not reasons:
            reasons.append("No suspicious prompt or sensitive-data indicators were detected.")

        risk_score = max(float(prompt_analysis.get("risk_score", 0.0)), float(data_leak_analysis.get("risk_score", 0.0)))
        if explicit_injection or sensitive_context:
            risk_score = max(risk_score, 0.7)

        if risk_score >= 0.8:
            risk_level = "HIGH"
            decision = "BLOCK"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
            decision = "REVIEW"
        else:
            risk_level = "LOW"
            decision = "ALLOW"

        if explicit_injection and risk_score < 0.8:
            decision = "REVIEW"

        if data_leak_analysis.get("has_sensitive_data") and risk_score >= 0.75:
            decision = "BLOCK"

        return {
            "request_id": self.generate_request_id(),
            "decision": decision,
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "prompt_analysis": prompt_analysis,
            "data_leak_analysis": data_leak_analysis,
            "reasons": reasons,
        }

    def scan_output_text(self, output_text: str) -> Dict[str, Any]:
        findings = []
        redacted_text = output_text

        for label, pattern in {
            "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            "PHONE": r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}",
            "API_KEY": r"(?i)(?:api[_-]?key|token|secret|password|access[_-]?key)[\s:=\"']+([A-Za-z0-9_\-]{12,})",
            "CONFIDENTIAL": r"(?i)(?:customer id|ssn|secret|private key|password)",
        }.items():
            matches = []
            compiled = __import__("re").compile(pattern)
            for match in compiled.finditer(output_text):
                matches.append(match.group(0))
            if matches:
                findings.append({"type": label, "count": len(matches), "examples": matches[:3]})
                for sample in matches[:3]:
                    redacted_text = redacted_text.replace(sample, "[REDACTED]")

        risk_score = min(1.0, len(findings) * 0.4)
        if risk_score >= 0.8:
            risk_level = "HIGH"
            decision = "BLOCK"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
            decision = "REVIEW"
        else:
            risk_level = "LOW"
            decision = "ALLOW"

        return {
            "request_id": self.generate_request_id(),
            "decision": decision,
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "findings": findings,
            "redacted_text": redacted_text,
            "reasons": ["Output contains sensitive material."] if findings else ["No sensitive output indicators detected."],
        }

    def scan_document(self, document_text: str) -> Dict[str, Any]:
        prompt_analysis = self.prompt_detector.detect(document_text)
        leak_analysis = self.data_leak_detector.detect(document_text)

        suspicious_findings = []
        sensitive_findings = []

        if prompt_analysis.get("is_suspicious"):
            suspicious_findings.append({"type": "prompt_injection", "risk_score": prompt_analysis.get("risk_score", 0.0), "detail": prompt_analysis.get("detection_reason")})
        if leak_analysis.get("has_sensitive_data"):
            for finding in leak_analysis.get("findings", []):
                sensitive_findings.append(finding)

        risk_score = max(float(prompt_analysis.get("risk_score", 0.0)), float(leak_analysis.get("risk_score", 0.0)))
        if risk_score >= 0.8:
            decision = "BLOCK"
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            decision = "REVIEW"
            risk_level = "MEDIUM"
        else:
            decision = "ALLOW"
            risk_level = "LOW"

        reasons = []
        if suspicious_findings:
            reasons.append("Suspicious embedded instructions detected.")
        if sensitive_findings:
            reasons.append("Sensitive material detected in document content.")
        if not reasons:
            reasons.append("Document content did not trigger injection or sensitive-data checks.")

        return {
            "request_id": self.generate_request_id(),
            "decision": decision,
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "suspicious_findings": suspicious_findings,
            "sensitive_findings": sensitive_findings,
            "reasons": reasons,
        }

    def evaluate_action(self, prompt: str, proposed_action: str, role: str, *, resource_context: dict | None = None, user_context: str = "mock-user", confirm_delete: bool = False) -> Dict[str, Any]:
        resource_context = resource_context or {}

        policy_result = self.policy_engine.evaluate_action(role, proposed_action, confirm_delete=confirm_delete)
        ml_result = self.prompt_detector.detect(prompt)
        leak_result = self.data_leak_detector.detect(prompt)

        auth = self.risk_engine.evaluate(prompt, role, proposed_action, confirm_delete=confirm_delete)
        risk_score = float(auth.get("overall_risk_score", 0.0))
        if risk_score >= 0.75:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if not policy_result["authorized"]:
            decision = "BLOCK"
            explanation = policy_result["reason"]
        elif not auth.get("authorized", True):
            decision = "BLOCK"
            explanation = auth.get("reason", "Blocked by security controls.")
        elif bool(ml_result.get("is_suspicious")) and proposed_action in {"update_simulated_record", "send_simulated_email", "delete_simulated_resource"}:
            decision = "BLOCK"
            explanation = "Prompt injection detection is suspicious for a sensitive action, so the action was blocked."
        elif bool(leak_result.get("has_sensitive_data")) and float(leak_result.get("risk_score", 0.0)) >= 0.75:
            decision = "BLOCK"
            explanation = "Sensitive information detected in the prompt; action is denied pending redaction and review."
        elif bool(ml_result.get("is_suspicious")) and self._contains_sensitive_resource_context(prompt):
            decision = "BLOCK"
            explanation = "The prompt references protected customer resources while ML scans show injection risk."
        elif bool(ml_result.get("is_suspicious")) and not self._looks_like_public_safe_request(prompt, proposed_action):
            decision = "REVIEW"
            explanation = "Prompt injection risk requires review before action authorization."
        elif bool(leak_result.get("has_sensitive_data")):
            decision = "REVIEW"
            explanation = "Sensitive information detected in the prompt; review required before proceeding."
        else:
            decision = "ALLOW"
            explanation = "Requested action is permitted under policy and accepted risk checks."

        return {
            "request_id": self.generate_request_id(),
            "decision": decision,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "policy_decision": policy_result,
            "detection_findings": {
                "ml_detection": ml_result,
                "data_leak_detection": leak_result,
            },
            "explanation": explanation,
        }
