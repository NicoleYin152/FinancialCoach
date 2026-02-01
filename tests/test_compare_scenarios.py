"""Eval tests for compare_scenarios: single and multi-delta application."""

from agent.action_executor import execute
from agent.capabilities import Capabilities
from agent.schemas.action import AgentAction
from agent.schemas.conversation import ConversationState


def test_compare_scenarios_multiple_deltas_applied():
    """Multiple expense deltas are applied cumulatively; scenario text mentions both."""
    baseline_input = {
        "monthly_income": 10000,
        "monthly_expenses": 5000,
        "expense_categories": [
            {"category": "Housing", "amount": 2000},
            {"category": "Transport", "amount": 1500},
            {"category": "Other", "amount": 1500},
        ],
    }
    state = ConversationState(
        conversation_id="test",
        turns=[],
        last_input_snapshot=baseline_input,
    )
    action = AgentAction(
        type="compare_scenarios",
        reasoning="User confirmed multi-line deltas",
        parameters={
            "deltas": [
                {"category": "Transport", "monthly_delta": 1500},
                {"category": "Dining", "monthly_delta": 500},
            ],
        },
    )
    trace = {}
    result = execute(
        action,
        state,
        baseline_input,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
        api_key=None,
        trace=trace,
    )
    assert result.get("action") == "compare_scenarios"
    assert result.get("message_type") == "scenario_result"
    # Both deltas applied: 5000 + 1500 + 500 = 7000
    ctx_before = result.get("context_before", {})
    ctx_after = result.get("context_after", {})
    assert ctx_before.get("total_expenses") == 5000
    assert ctx_after.get("total_expenses") == 7000
    msg = result.get("assistant_message", "")
    assert "Transport" in msg and "Dining" in msg
    assert "Scenario analyzed with changes" in msg
