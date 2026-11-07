from __future__ import annotations

from backend.evaluation.generate_scenarios import build_scenarios


def test_generated_scenario_suite_is_unique_and_has_expected_fields() -> None:
    scenarios = build_scenarios()
    assert len(scenarios) >= 100
    assert len({scenario["scenario_id"] for scenario in scenarios}) == len(scenarios)
    prompts = {
        f"{scenario['user_request']}\n{scenario['document_content'] or ''}".strip().casefold()
        for scenario in scenarios
    }
    assert len(prompts) == len(scenarios)
    assert all(scenario["expected_authorization_outcome"] in {"ALLOW", "DENY"} for scenario in scenarios)
    assert all(isinstance(scenario["expected_malicious"], bool) for scenario in scenarios)
    assert all(
        scenario["proposed_action"] in {
            "search_public_documents",
            "read_customer_record",
            "send_simulated_email",
            "update_simulated_record",
            "delete_simulated_resource",
        }
        for scenario in scenarios
    )
