"""Eval tests for planner: fallback on invalid LLM output."""

from unittest.mock import MagicMock, patch

from tools.context import FinancialContext
from agent.planner import select_tools


def _mock_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    return MagicMock(choices=[choice])


def test_planner_fallback_on_invalid_llm_output():
    """Planner falls back to all tools when LLM returns invalid JSON."""
    ctx = FinancialContext.from_api_input(
        {"monthly_income": 8000, "monthly_expenses": 5500}
    )
    trace = {}

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = _mock_response(
            "Here is my analysis: you should run expense_ratio"
        )
        selected = select_tools(
            ctx,
            capabilities_agent=True,
            api_key="sk-fake",
            trace=trace,
        )

    assert trace["planner_status"] == "fallback"
    assert "expense_ratio" in selected
    assert "expense_concentration" in selected
    assert "asset_concentration" in selected
    assert "liquidity" in selected


def test_planner_fallback_on_empty_llm_output():
    """Planner falls back when LLM returns empty content."""
    ctx = FinancialContext.from_api_input(
        {"monthly_income": 8000, "monthly_expenses": 5500}
    )
    trace = {}

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = _mock_response("")
        selected = select_tools(
            ctx,
            capabilities_agent=True,
            api_key="sk-fake",
            trace=trace,
        )

    assert trace["planner_status"] == "fallback"
    assert len(selected) >= 1


def test_planner_skipped_when_agent_disabled():
    """Planner is skipped when capabilities.agent is False."""
    ctx = FinancialContext.from_api_input(
        {"monthly_income": 8000, "monthly_expenses": 5500}
    )
    trace = {}

    selected = select_tools(
        ctx,
        capabilities_agent=False,
        api_key="sk-fake",
        trace=trace,
    )

    assert trace["planner_status"] == "skipped"
    assert trace["planner_used"] is False
    assert "expense_ratio" in selected


def test_planner_valid_parses_json():
    """Planner parses valid JSON and returns selected tools."""
    ctx = FinancialContext.from_api_input(
        {"monthly_income": 8000, "monthly_expenses": 5500}
    )
    trace = {}

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = _mock_response(
            '{"tools": ["expense_ratio"]}'
        )
        selected = select_tools(
            ctx,
            capabilities_agent=True,
            api_key="sk-fake",
            trace=trace,
        )

    assert trace["planner_status"] == "valid"
    assert selected == ["expense_ratio"]
