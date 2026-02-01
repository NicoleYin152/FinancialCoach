"""Eval tests for agent actions: schema validation, fallback, execution."""

from unittest.mock import MagicMock, patch

from agent.action_executor import execute
from agent.action_planner import select_action, _default_action
from agent.capabilities import Capabilities
from agent.schemas.action import AgentAction
from agent.schemas.conversation import ConversationState, ConversationTurn
from tools.context import FinancialContext
from tools.registry import run_tools


def _mock_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    return MagicMock(choices=[choice])


def test_action_schema_rejects_invalid():
    """AgentAction rejects invalid action types."""
    from pydantic import ValidationError

    try:
        AgentAction.model_validate_json('{"type": "invalid_action", "reasoning": "", "parameters": {}}')
        assert False, "Should have raised"
    except Exception as e:
        assert "type" in str(e).lower() or "validation" in str(e).lower()


def test_action_planner_noop_on_invalid_llm():
    """Planner returns noop on invalid LLM output (no silent heuristic fallback)."""
    state = ConversationState(
        conversation_id="test",
        turns=[ConversationTurn(role="user", content="hello")],
    )
    trace = {}
    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = _mock_response(
            "Here is my advice: you should invest in stocks"
        )
        action = select_action(state, "sk-fake", trace)

    assert trace["action_planner_status"] in ("invalid_or_error", "fallback_no_llm")
    assert action.type in ("run_analysis", "explain_previous", "compare_scenarios", "clarifying_question", "noop")


def test_execute_run_analysis_with_valid_input():
    """Execute run_analysis with complete input triggers orchestrator."""
    state = ConversationState(conversation_id="t1", turns=[])
    input_data = {"monthly_income": 8000, "monthly_expenses": 5500}
    caps = Capabilities(llm=False, retry=False, fallback=False, agent=False)
    trace = {}

    result = execute(
        AgentAction(type="run_analysis", reasoning="", parameters={}),
        state,
        input_data,
        caps,
        None,
        trace,
    )

    assert result["action"] == "run_analysis"
    assert result["run_id"] is not None
    assert len(result["analysis"]) >= 0
    assert "assistant_message" in result


def test_execute_run_analysis_incomplete_input_asks_clarifying():
    """Execute run_analysis with incomplete input returns clarifying question."""
    state = ConversationState(conversation_id="t2", turns=[])
    input_data = {"monthly_income": 8000}  # missing expenses
    caps = Capabilities(llm=False, retry=False, fallback=False, agent=False)
    trace = {}

    result = execute(
        AgentAction(type="run_analysis", reasoning="", parameters={}),
        state,
        input_data,
        caps,
        None,
        trace,
    )

    assert result["action"] == "run_analysis"
    assert result["run_id"] is None
    assert result["message_type"] == "clarifying_question"
    assert "income" in result["assistant_message"].lower() or "expense" in result["assistant_message"].lower()


def test_execute_noop_returns_neutral():
    """Execute noop returns minimal message (no generic help text)."""
    state = ConversationState(
        conversation_id="t3",
        turns=[ConversationTurn(role="user", content="hello world")],
    )
    trace = {}

    result = execute(
        AgentAction(type="noop", reasoning="Unrelated", parameters={}),
        state,
        None,
        Capabilities(llm=False, retry=False, fallback=False, agent=False),
        None,
        trace,
    )

    assert result["action"] == "noop"
    assert "understand" in result["assistant_message"].lower() or "unrelated" in result["assistant_message"].lower()
