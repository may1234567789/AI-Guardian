from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping

from backend.agent.mock_tools import (
    delete_simulated_resource,
    read_customer_record,
    search_public_documents,
    send_simulated_email,
    update_simulated_record,
)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    allowed_arguments: Dict[str, Any]
    required_permissions: tuple[str, ...]
    resource_requirements: tuple[str, ...]
    risk_classification: str
    executor: Callable[..., Dict[str, Any]]


class ToolRegistry:
    """Controlled registry of tools the simulated agent may invoke."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {
            "search_public_documents": ToolDefinition(
                name="search_public_documents",
                description="Search a small collection of public documentation and FAQs.",
                allowed_arguments={
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "required": False, "default": 5},
                },
                required_permissions=("search_public_documents",),
                resource_requirements=(),
                risk_classification="LOW",
                executor=search_public_documents,
            ),
            "read_customer_record": ToolDefinition(
                name="read_customer_record",
                description="Read a synthetic customer record only when the caller is authorized and the resource is scoped correctly.",
                allowed_arguments={
                    "customer_id": {"type": "string", "required": True},
                    "fields": {"type": "list", "required": False, "default": None},
                },
                required_permissions=("read_customer_record",),
                resource_requirements=("customer_id",),
                risk_classification="MEDIUM",
                executor=read_customer_record,
            ),
            "send_simulated_email": ToolDefinition(
                name="send_simulated_email",
                description="Create a simulated email message without sending a real email.",
                allowed_arguments={
                    "recipient": {"type": "string", "required": True},
                    "subject": {"type": "string", "required": True},
                    "body": {"type": "string", "required": True},
                },
                required_permissions=("send_simulated_email",),
                resource_requirements=("recipient",),
                risk_classification="MEDIUM",
                executor=send_simulated_email,
            ),
            "update_simulated_record": ToolDefinition(
                name="update_simulated_record",
                description="Update a synthetic customer or system record in mock storage.",
                allowed_arguments={
                    "customer_id": {"type": "string", "required": True},
                    "field": {"type": "string", "required": True},
                    "value": {"type": "string", "required": True},
                },
                required_permissions=("update_simulated_record",),
                resource_requirements=("customer_id",),
                risk_classification="HIGH",
                executor=update_simulated_record,
            ),
            "delete_simulated_resource": ToolDefinition(
                name="delete_simulated_resource",
                description="Delete a synthetic resource only with policy approval and explicit confirmation.",
                allowed_arguments={
                    "resource_id": {"type": "string", "required": True},
                    "resource_type": {"type": "string", "required": True},
                    "confirm_delete": {"type": "boolean", "required": True},
                },
                required_permissions=("delete_simulated_resource",),
                resource_requirements=("resource_id", "resource_type"),
                risk_classification="HIGH",
                executor=delete_simulated_resource,
            ),
        }

    def get_tool(self, tool_name: str) -> ToolDefinition:
        if tool_name not in self._tools:
            raise KeyError(f"Unknown tool '{tool_name}'.")
        return self._tools[tool_name]

    def is_registered(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def validate_arguments(self, tool_name: str, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        cleaned: Dict[str, Any] = {}
        for key, spec in tool.allowed_arguments.items():
            if spec.get("required") and key not in arguments:
                raise ValueError(f"Missing required argument '{key}' for tool '{tool_name}'.")
            if key in arguments:
                value = arguments[key]
                if spec["type"] == "string" and not isinstance(value, str):
                    raise TypeError(f"Argument '{key}' for tool '{tool_name}' must be a string.")
                if spec["type"] == "integer" and not isinstance(value, int):
                    raise TypeError(f"Argument '{key}' for tool '{tool_name}' must be an integer.")
                if spec["type"] == "boolean" and not isinstance(value, bool):
                    raise TypeError(f"Argument '{key}' for tool '{tool_name}' must be a boolean.")
                if spec["type"] == "list" and not isinstance(value, list):
                    raise TypeError(f"Argument '{key}' for tool '{tool_name}' must be a list.")
                cleaned[key] = value
        return cleaned

    def execute(self, tool_name: str, arguments: Mapping[str, Any], *, role: str, resource_context: Mapping[str, Any] | None = None, confirm_delete: bool = False) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        validated = self.validate_arguments(tool_name, dict(arguments or {}))
        if resource_context is None:
            resource_context = {}
        required_resources = set(tool.resource_requirements)
        if required_resources and not required_resources.issubset(resource_context.keys()):
            missing = sorted(required_resources - set(resource_context.keys()))
            raise ValueError(f"Tool '{tool_name}' requires resource context for {missing}.")
        if role not in {"admin", "analyst", "viewer"}:
            raise PermissionError(f"Unknown role '{role}' for tool '{tool_name}'.")
        if tool.name not in {"search_public_documents"} and role == "viewer":
            raise PermissionError("Viewer role is not permitted to invoke protected tools.")
        if tool.name == "delete_simulated_resource" and not confirm_delete:
            raise PermissionError("Destructive resource deletes require explicit confirmation before execution.")
        return tool.executor(**validated)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for name, tool in self._tools.items():
            result[name] = {
                "description": tool.description,
                "allowed_arguments": tool.allowed_arguments,
                "required_permissions": list(tool.required_permissions),
                "resource_requirements": list(tool.resource_requirements),
                "risk_classification": tool.risk_classification,
            }
        return result


DEFAULT_TOOL_REGISTRY = ToolRegistry()

__all__ = ["ToolDefinition", "ToolRegistry", "DEFAULT_TOOL_REGISTRY"]
