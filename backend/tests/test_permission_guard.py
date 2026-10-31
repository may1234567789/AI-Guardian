from backend.security.permission_guard import PermissionGuard


def test_permission_guard_blocks_unauthorized_action():
    guard = PermissionGuard()
    decision = guard.authorize("Please summarize customer support logs.", "viewer", "read_customer_record")
    assert decision["authorized"] is False


def test_permission_guard_allows_safe_action():
    guard = PermissionGuard()
    decision = guard.authorize("Search the public product knowledge base.", "analyst", "search_public_documents")
    assert decision["authorized"] is True
