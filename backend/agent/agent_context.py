from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentContext:
    user_request: str
    trusted_user_context: str = "mock-user"
    user_role: str = "analyst"
    document_context: Optional[str] = None
    resource_context: Dict[str, Any] = field(default_factory=dict)
    confirm_delete: bool = False
    source: str = "simulated-agent"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "user_request": self.user_request,
            "trusted_user_context": self.trusted_user_context,
            "user_role": self.user_role,
            "document_context": self.document_context,
            "resource_context": self.resource_context,
            "confirm_delete": self.confirm_delete,
            "source": self.source,
        }


__all__ = ["AgentContext"]
