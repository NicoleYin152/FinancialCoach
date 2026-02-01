"""Eval tests for orchestrator: deterministic run, replay consistency."""

from agent.capabilities import Capabilities
from agent.memory import RUN_HISTORY, RunMemory
from agent.orchestrator import run


def test_deterministic_run_with_agent_disabled():
    """Run with agent disabled is deterministic (no LLM planner)."""
    input_data = {"monthly_income": 8000, "monthly_expenses": 5500}
    caps = Capabilities(llm=False, retry=False, fallback=False, agent=False)

    result1 = run(input_data, capabilities=caps)
    result2 = run(input_data, capabilities=caps)

    assert result1["trace"]["planner_status"] == "skipped"
    assert result2["trace"]["planner_status"] == "skipped"
    assert len(result1["analysis"]) == len(result2["analysis"])
    for a1, a2 in zip(result1["analysis"], result2["analysis"]):
        assert a1["dimension"] == a2["dimension"]
        assert a1["risk_level"] == a2["risk_level"]
        assert a1["reason"] == a2["reason"]


def test_run_returns_run_id():
    """Successful run returns run_id."""
    result = run(
        {"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert "run_id" in result
    assert result["run_id"] is not None
    assert isinstance(result["run_id"], str)
    assert len(result["run_id"]) > 0


def test_replay_consistency():
    """Replay returns same data as original run."""
    result = run(
        {"monthly_income": 5000, "monthly_expenses": 4600},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    run_id = result["run_id"]
    assert run_id is not None

    memory = RUN_HISTORY.get(run_id)
    assert memory is not None
    assert isinstance(memory, RunMemory)
    assert memory.run_id == run_id
    assert memory.tools_selected == result["trace"]["tools_selected"]
    assert len(memory.tool_results) == len(result["analysis"])
    assert "income" in memory.context_snapshot
    assert "total_expenses" in memory.context_snapshot


def test_failed_run_no_memory():
    """Failed run (validation error) does not store memory."""
    initial_len = len(RUN_HISTORY)
    result = run(
        {"monthly_income": -100, "monthly_expenses": 50},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert result["run_id"] is None
    assert "input_validation_failed" in result["trace"]["phases"]
    assert len(RUN_HISTORY) == initial_len
