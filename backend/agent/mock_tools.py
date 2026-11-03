from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping

PUBLIC_DOCUMENTS = [
    {
        "id": "public-doc-1",
        "title": "Public FAQ",
        "content": "The public support FAQ explains that employees may search public documentation and onboarding guides.",
    },
    {
        "id": "public-doc-2",
        "title": "Onboarding Guide",
        "content": "New staff should review the public onboarding guide before accessing internal customer systems.",
    },
    {
        "id": "public-doc-3",
        "title": "Security Awareness",
        "content": "Never share credentials in public chat. Report suspicious messages to the security team.",
    },
]

CUSTOMER_RECORDS = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "status": "active",
        "notes": "Prefers email communication and a standard support plan.",
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "name": "Marcus Chen",
        "email": "marcus@example.com",
        "status": "pending",
        "notes": "Needs verification before invoice changes.",
    },
}

SIMULATED_EMAILS: List[Dict[str, Any]] = []
RESOURCE_STORE: Dict[str, Dict[str, Any]] = {
    "resource-001": {
        "resource_id": "resource-001",
        "resource_type": "customer-notes",
        "status": "active",
    },
    "resource-002": {
        "resource_id": "resource-002",
        "resource_type": "knowledge-base",
        "status": "active",
    },
}


def search_public_documents(*, query: str, limit: int = 5) -> Dict[str, Any]:
    filtered = []
    lowered = (query or "").lower()
    for doc in PUBLIC_DOCUMENTS:
        haystack = f"{doc['title']} {doc['content']}".lower()
        if not lowered or lowered in haystack:
            filtered.append({"id": doc["id"], "title": doc["title"], "content": doc["content"]})
    return {"tool": "search_public_documents", "query": query, "count": min(len(filtered), limit), "results": filtered[:limit]}


def read_customer_record(*, customer_id: str, fields: Iterable[str] | None = None) -> Dict[str, Any]:
    if customer_id not in CUSTOMER_RECORDS:
        raise KeyError(f"Customer record '{customer_id}' was not found.")
    record = deepcopy(CUSTOMER_RECORDS[customer_id])
    requested_fields = list(fields) if fields is not None else sorted(record.keys())
    subset = {key: record.get(key) for key in requested_fields if key in record}
    return {"tool": "read_customer_record", "customer_id": customer_id, "record": subset}


def send_simulated_email(*, recipient: str, subject: str, body: str) -> Dict[str, Any]:
    email = {
        "tool": "send_simulated_email",
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": "queued",
        "delivery": "simulated",
    }
    SIMULATED_EMAILS.append(email)
    return email


def update_simulated_record(*, customer_id: str, field: str, value: str) -> Dict[str, Any]:
    if customer_id not in CUSTOMER_RECORDS:
        raise KeyError(f"Customer record '{customer_id}' was not found.")
    record = CUSTOMER_RECORDS[customer_id]
    old_value = record.get(field)
    record[field] = value
    return {
        "tool": "update_simulated_record",
        "customer_id": customer_id,
        "field": field,
        "previous_value": old_value,
        "new_value": value,
        "status": "updated",
    }


def delete_simulated_resource(*, resource_id: str, resource_type: str, confirm_delete: bool) -> Dict[str, Any]:
    if not confirm_delete:
        raise PermissionError("delete_simulated_resource requires explicit confirmation before execution.")
    if resource_id not in RESOURCE_STORE:
        raise KeyError(f"Resource '{resource_id}' was not found.")
    resource = RESOURCE_STORE.pop(resource_id)
    return {
        "tool": "delete_simulated_resource",
        "resource_id": resource_id,
        "resource_type": resource_type,
        "deleted_resource": resource,
        "status": "deleted",
    }


__all__ = [
    "PUBLIC_DOCUMENTS",
    "CUSTOMER_RECORDS",
    "SIMULATED_EMAILS",
    "RESOURCE_STORE",
    "search_public_documents",
    "read_customer_record",
    "send_simulated_email",
    "update_simulated_record",
    "delete_simulated_resource",
]
