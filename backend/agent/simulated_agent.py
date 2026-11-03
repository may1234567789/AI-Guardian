from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from backend.agent.agent_context import AgentContext
from backend.agent.document_processor import DocumentProcessor
from backend.agent.tool_registry import DEFAULT_TOOL_REGISTRY
from backend.security.data_leak_detector import DataLeakDetector
from backend.security.permission_guard import PermissionGuard
from backend.security.policy_engine import PolicyEngine
from backend.security.prompt_detector import PromptDetector


class SimulatedAgent:
    """Deterministic mock agent that uses SentinelAI controls before any tool execution."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        prompt_detector: Optional[PromptDetector] = None,
        leak_detector: Optional[DataLeakDetector] = None,
        permission_guard: Optional[PermissionGuard] = None,
        tool_registry: Optional[Any] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.prompt_detector = prompt_detector or PromptDetector()
        self.leak_detector = leak_detector or DataLeakDetector()
        self.permission_guard = permission_guard or PermissionGuard(policy_engine=self.policy_engine, prompt_detector=self.prompt_detector)
        self.tool_registry = tool_registry or DEFAULT_TOOL_REGISTRY
        self.document_processor = DocumentProcessor()

    @staticmethod
    def _build_request_id() -> str:
        return f"agent-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _resolve_action(user_request: str, document_context: Optional[str] = None) -> str:
        lowered = (user_request + " " + (document_context or "")).lower()
        if "email" in lowered and "send" in lowered:
            return "send_simulated_email"
        if "update" in lowered and "record" in lowered:
            return "update_simulated_record"
        if "delete" in lowered:
            return "delete_simulated_resource"
        if "customer" in lowered and "record" in lowered or "customer profile" in lowered:
            return "read_customer_record"
        if "public" in lowered or "faq" in lowered or "onboarding" in lowered:
            return "search_public_documents"
        return "search_public_documents"

    @staticmethod
    def _default_resource_context_for_action(action: str, user_request: str) -> Dict[str, Any]:
        if action == "read_customer_record":
            return {"customer_id": "CUST-1001"}
        if action == "send_simulated_email":
            return {"recipient": "ops@example.com"}
        if action == "update_simulated_record":
            return {"customer_id": "CUST-1001", "field": "status", "value": "updated"}
        if action == "delete_simulated_resource":
            return {"resource_id": "resource-001", "resource_type": "customer-notes"}
        return {"collection": "public-documents"}

    def _compile_action_arguments(self, action: str, user_request: str, resource_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "search_public_documents":
            return {"query": user_request, "limit": 3}
        if action == "read_customer_record":
            customer_id = resource_context.get("customer_id", "CUST-1001")
            return {"customer_id": customer_id, "fields": ["customer_id", "name", "email", "status"]}
        if action == "send_simulated_email":
            return {
                "recipient": resource_context.get("recipient", "ops@example.com"),
                "subject": "SentinelAI action review",
                "body": user_request,
            }
        if action == "update_simulated_record":
            return {
                "customer_id": resource_context.get("customer_id", "CUST-1001"),
                "field": resource_context.get("field", "status"),
                "value": resource_context.get("value", "updated"),
            }
        if action == "delete_simulated_resource":
            return {
                "resource_id": resource_context.get("resource_id", "resource-001"),
                "resource_type": resource_context.get("resource_type", "customer-notes"),
                "confirm_delete": True,
            }
        return {"query": user_request, "limit": 3}

    def _evaluate_document_context(self, document_context: Optional[str]) -> Dict[str, Any]:
        if not document_context:
            return {"document_risk": 0.0, "decision": "ALLOW", "sources": []}
        processed = self.document_processor.process(document_context)
        doc_risk = self.prompt_detector.detect(document_context)
        leak = self.leak_detector.detect(document_context)
        risk = max(float(doc_risk.get("risk_score", 0.0)), float(leak.get("risk_score", 0.0)))
        if doc_risk.get("is_suspicious") or leak.get("has_sensitive_data") or processed["instruction_like_sentences"]:
            return {"document_risk": risk, "decision": "BLOCK", "sources": [processed], "ml_result": doc_risk, "leak_result": leak}
        return {"document_risk": risk, "decision": "ALLOW", "sources": [processed], "ml_result": doc_risk, "leak_result": leak}

    def process_request(self, user_request: str, trusted_user_context: str = "mock-user", *, user_role: str = "analyst", document_context: Optional[str] = None, resource_context: Optional[Dict[str, Any]] = None, confirm_delete: bool = False) -> Dict[str, Any]:
        request_id = self._build_request_id()
        resource_context = resource_context or {}
        action = self._resolve_action(user_request, document_context)
        action_context = {**self._default_resource_context_for_action(action, user_request), **resource_context}
        arguments = self._compile_action_arguments(action, user_request, action_context)

        combined_prompt = user_request
        if document_context:
            combined_prompt = f"{user_request}\n{document_context}"

        security_decision = self.permission_guard.authorize(
            combined_prompt,
            user_role,
            action,
            confirm_delete=confirm_delete,
        )

        if not security_decision["authorized"]:
            return {
                "request_id": request_id,
                "status": "completed",
                "security_decision": "BLOCK",
                "proposed_action": action,
                "tool_executed": False,
                "tool_result": {},
                "risk_score": float(security_decision.get("ml_detection", {}).get("risk_score", 0.0)),
                "risk_level": "HIGH" if float(security_decision.get("ml_detection", {}).get("risk_score", 0.0)) >= 0.7 else "MEDIUM",
                "explanation": security_decision.get("reason", "Authorization denied before execution."),
                "action_arguments": arguments,
            }

        tool_result = self.tool_registry.execute(action, arguments, role=user_role, resource_context=action_context, confirm_delete=confirm_delete)

        output_scan = self.leak_detector.detect(str(tool_result))
        if output_scan.get("has_sensitive_data"):
            redacted = "[REDACTED]"
            tool_result = {"tool": tool_result.get("tool"), "status": "redacted", "message": redacted}
            return {
                "request_id": request_id,
                "status": "completed",
                "security_decision": "BLOCK",
                "proposed_action": action,
                "tool_executed": False,
                "tool_result": tool_result,
                "risk_score": float(output_scan.get("risk_score", 0.0)),
                "risk_level": "HIGH" if float(output_scan.get("risk_score", 0.0)) >= 0.75 else "MEDIUM",
                "explanation": "Sensitive output was detected and blocked before returning tool results.",
                "action_arguments": arguments,
            }

        return {
            "request_id": request_id,
            "status": "completed",
            "security_decision": "ALLOW",
            "proposed_action": action,
            "tool_executed": True,
            "tool_result": tool_result,
            "risk_score": float(security_decision.get("ml_detection", {}).get("risk_score", 0.0)),
            "risk_level": "LOW" if float(security_decision.get("ml_detection", {}).get("risk_score", 0.0)) < 0.4 else "MEDIUM",
            "explanation": "The action was authorized and executed under SentinelAI controls.",
            "action_arguments": arguments,
        }


__all__ = ["SimulatedAgent"]
