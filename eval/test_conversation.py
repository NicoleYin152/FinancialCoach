"""Eval tests for conversation orchestrator: multi-turn, state, replay."""

from agent.capabilities import Capabilities
from agent.conversation_orchestrator import chat
from agent.conversation_store import CONVERSATION_HISTORY


def test_chat_returns_conversation_id():
    """Chat returns conversation_id in response."""
    result = chat(
        message="I make 8000 and spend 5500",
        input_data={"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert "conversation_id" in result
    assert result["conversation_id"] is not None
    assert len(result["conversation_id"]) > 0


def test_chat_with_input_runs_analysis():
    """Chat with valid financial input runs analysis."""
    result = chat(
        message="Analyze my finances",
        input_data={"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert result["run_id"] is not None
    assert "assistant_message" in result
    assert "analysis" in result


def test_chat_multi_turn_preserves_state():
    """Multi-turn chat preserves conversation state."""
    cid = "eval-multiturn-001"
    if cid in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[cid]

    r1 = chat(
        message="I make 8000 and spend 5500",
        conversation_id=cid,
        input_data={"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r1["run_id"] is not None

    r2 = chat(
        message="Why is my savings rate low?",
        conversation_id=cid,
        input_data={"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert r2["conversation_id"] == cid
    assert r2["run_id"] == r1["run_id"] or r2["assistant_message"]  # explain reuses run
    assert len(CONVERSATION_HISTORY[cid].turns) >= 4  # 2 user + 2 assistant


def test_chat_no_input_asks_clarifying():
    """Chat without financial input asks for clarification."""
    result = chat(
        message="Can you analyze my finances?",
        input_data=None,
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert result["run_id"] is None
    assert "income" in result["assistant_message"].lower() or "expense" in result["assistant_message"].lower()
