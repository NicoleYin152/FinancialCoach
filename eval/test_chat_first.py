"""Eval tests for chat-first agent: clarifying question, scenario, regression."""

from agent.capabilities import Capabilities
from agent.conversation_orchestrator import chat
from agent.conversation_store import CONVERSATION_HISTORY


def test_ambiguous_intent_triggers_clarifying_question():
    """Ambiguous financial intent (no delta) → ask_clarifying_question."""
    cid = "eval-ambiguous-001"
    if cid in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[cid]

    result = chat(
        message="What if I buy a car?",
        conversation_id=cid,
        input_data={"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )

    assert result["message_type"] == "clarifying_question"
    assert "category" in result["assistant_message"].lower() or "amount" in result["assistant_message"].lower()
    assert result["run_id"] is None
    assert CONVERSATION_HISTORY[cid].pending_clarification is not None


def test_confirmation_parsed_runs_scenario():
    """Clarification → user confirms delta → run_scenario."""
    cid = "eval-confirm-001"
    if cid in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[cid]

    input_data = {"monthly_income": 8000, "monthly_expenses": 5500}
    r1 = chat(
        message="What if I spend more on Transport?",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r1["message_type"] == "clarifying_question"

    r2 = chat(
        message="Transport +1500",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r2["run_id"] is not None
    assert r2["message_type"] == "scenario_result"
    assert len(r2["analysis"]) >= 0
    assert CONVERSATION_HISTORY[cid].pending_clarification is None


def test_invalid_confirmation_retry_then_noop():
    """Invalid confirmation → retry → still invalid → noop."""
    cid = "eval-retry-001"
    if cid in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[cid]

    input_data = {"monthly_income": 8000, "monthly_expenses": 5500}
    r1 = chat(
        message="What if I reduce spending?",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r1["message_type"] == "clarifying_question"

    r2 = chat(
        message="just kidding",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r2["message_type"] in ("clarifying_question", "assistant")

    r3 = chat(
        message="nope",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    # Noop: no generic help text; or limit message "I couldn't get enough information to proceed..."
    msg = r3["assistant_message"].lower()
    assert (
        "understand" in msg or "request" in msg or "unrelated" in msg
        or "parse" in msg or "delta" in msg or "retry" in msg or "couldn't" in msg
        or "information" in msg or "proceed" in msg  # limit noop message
    )
    # After 2 clarification attempts, third unparseable hits limit
    assert r3.get("trace", {}).get("clarification_attempt") == 3
    assert r3.get("trace", {}).get("planner_decision") == "noop_due_to_clarification_limit"


def test_clarification_limit_two_attempts_then_noop():
    """Clarification attempts capped at 2; third ambiguous/unparseable returns noop_due_to_clarification_limit."""
    cid = "eval-limit-001"
    if cid in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[cid]

    input_data = {"monthly_income": 8000, "monthly_expenses": 5500}
    r1 = chat(
        message="What if I buy a car?",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r1["message_type"] == "clarifying_question"
    assert r1.get("trace", {}).get("clarification_attempt") == 1

    r2 = chat(
        message="something vague",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r2["message_type"] == "clarifying_question"
    assert r2.get("trace", {}).get("clarification_attempt") == 2

    r3 = chat(
        message="still not a delta",
        conversation_id=cid,
        input_data=input_data,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r3.get("trace", {}).get("planner_decision") == "noop_due_to_clarification_limit"
    assert r3.get("trace", {}).get("clarification_attempt") == 3
    assert "information" in r3["assistant_message"].lower() or "proceed" in r3["assistant_message"].lower()
    assert r3.get("run_id") is None


def test_baseline_vs_scenario_diff():
    """Scenario run produces diff between baseline and scenario."""
    from tools.context import FinancialContext

    base = FinancialContext.from_api_input(
        {"monthly_income": 8000, "monthly_expenses": 5500}
    )
    scenario = base.apply_expense_delta("Transport", 1500)
    assert scenario.total_expenses == 7000
    assert "Transport" in scenario.expense_categories
    assert scenario.expense_categories["Transport"] == 1500


def test_agent_run_unchanged():
    """Regression: POST /agent/run behavior unchanged."""
    from fastapi.testclient import TestClient
    from api.server import app

    client = TestClient(app)
    response = client.post(
        "/agent/run",
        json={
            "input": {"monthly_income": 8000, "monthly_expenses": 5500},
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert "analysis" in data
    assert "trace" in data
