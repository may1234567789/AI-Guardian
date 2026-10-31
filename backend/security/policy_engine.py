"""Deterministic policy engine for permitted AI-agent actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


class PolicyEngine:
    """Authoritative role-based policy decision engine."""

    def __init__(self, policy_path: str | None = None):
        self.policy_path = Path(policy_path) if policy_path else self._default_policy_path()
        self._policy = self._load_policy()

    @staticmethod
    def _default_policy_path() -> Path:
        return Path(__file__).resolve().parents[1] / "config" / "security_policies.json"

    def _load_policy(self) -> dict:
        with self.policy_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @property
    def roles(self) -> Dict[str, set[str]]:
        return {role: set(details.get("allowed_actions", [])) for role, details in self._policy.get("roles", {}).items()}

    @property
    def actions(self) -> set[str]:
        return set(self._policy.get("actions", {}).keys())

    def is_role_recognized(self, role: str) -> bool:
        return role in self._policy.get("roles", {})

    def is_action_recognized(self, action: str) -> bool:
        return action in self._policy.get("actions", {})

    def is_action_permitted(self, role: str, action: str) -> bool:
        if not self.is_role_recognized(role):
            return False
        if not self.is_action_recognized(action):
            return False
        return action in self.roles.get(role, set())

    def evaluate_action(self, role: str, action: str, *, confirm_delete: bool = False) -> Dict[str, object]:
        """Return a policy decision object with the final authorization result."""
        if not self.is_role_recognized(role):
            return {
                "authorized": False,
                "role": role,
                "action": action,
                "reason": f"Unknown role '{role}'.",
            }
        if not self.is_action_recognized(action):
            return {
                "authorized": False,
                "role": role,
                "action": action,
                "reason": f"Unknown action '{action}'.",
            }

        if action not in self.roles.get(role, set()):
            return {
                "authorized": False,
                "role": role,
                "action": action,
                "reason": f"Role '{role}' is not permitted to perform '{action}'.",
            }

        requires_confirmation = self._policy.get("actions", {}).get(action, {}).get("requires_confirmation", False)
        if requires_confirmation and not confirm_delete:
            return {
                "authorized": False,
                "role": role,
                "action": action,
                "reason": "Deletion requires explicit confirmation before authorization.",
            }

        return {
            "authorized": True,
            "role": role,
            "action": action,
            "reason": "Authorized by the deterministic policy engine.",
        }

    def get_permission_summary(self) -> Dict[str, Dict[str, bool]]:
        summary: Dict[str, Dict[str, bool]] = {}
        for role, actions in self.roles.items():
            summary[role] = {action: action in actions for action in sorted(self.actions)}
        return summary

    def __contains__(self, item: str) -> bool:
        return item in self.actions
