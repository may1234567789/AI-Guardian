"""Security context for agent action requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SecurityContext:
    """Encapsulates the role, action, and request metadata for action authorization."""

    role: str
    action: str
    prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    require_confirmation: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "action": self.action,
            "prompt": self.prompt,
            "require_confirmation": self.require_confirmation,
            "metadata": dict(self.metadata),
        }
