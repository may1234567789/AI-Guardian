from backend.security.policy_engine import PolicyEngine


def test_admin_can_perform_high_privilege_action():
    engine = PolicyEngine()
    assert engine.is_action_permitted("admin", "send_simulated_email") is True
    assert engine.evaluate_action("admin", "read_customer_record")["authorized"] is True


def test_viewer_cannot_read_customer_record():
    engine = PolicyEngine()
    decision = engine.evaluate_action("viewer", "read_customer_record")
    assert decision["authorized"] is False


def test_delete_requires_explicit_confirmation():
    engine = PolicyEngine()
    decision = engine.evaluate_action("admin", "delete_simulated_resource", confirm_delete=False)
    assert decision["authorized"] is False
