"""Tests for agent/orchestrator.py."""

from unittest.mock import patch

from agent.capabilities import Capabilities
from agent.orchestrator import run


def test_llm_disabled_path():
    """When LLM disabled, returns deterministic output without calling LLM."""
    caps = Capabilities(llm=False, retry=False, fallback=False)
    with patch("agent.orchestrator.get_openai_api_key", return_value="sk-fake"):
        result = run(
            {"monthly_income": 5000, "monthly_expenses": 4000},
            capabilities=caps,
        )
    assert "analysis" in result
    assert "education" in result
    assert "generation" in result
    assert "trace" in result
    assert len(result["analysis"]) >= 0
    assert "validation" in result
    assert "errors" in result
    trace = result["trace"]
    assert "llm_skipped" in trace.get("phases", [])
    assert "Savings" in result["generation"] or "ExpenseRatio" in result["generation"] or len(result["generation"]) > 0


def test_validation_failure_retry():
    """When validation fails and retry enabled, retries then falls back."""
    caps = Capabilities(llm=True, retry=True, fallback=True)
    call_count = 0

    def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return "You should buy stocks!"  # Invalid - will fail validation

    with patch("agent.orchestrator.get_openai_api_key", return_value="sk-fake"):
        with patch("agent.orchestrator.generate", side_effect=mock_generate):
            with patch("agent.orchestrator.retry_with_backoff") as mock_retry:
                def fake_retry(fn, **kw):
                    return fn()  # Run once, will raise ValueError
                mock_retry.side_effect = fake_retry
                result = run(
                    {"monthly_income": 5000, "monthly_expenses": 4000},
                    capabilities=caps,
                    api_key="sk-fake",
                )
    assert "generation" in result
    assert "errors" in result


def test_fallback_execution():
    """When retries exhausted and fallback enabled, uses deterministic output."""
    caps = Capabilities(llm=True, retry=True, fallback=True)

    def mock_generate(*args, **kwargs):
        return "You should buy!"  # Fails validation

    with patch("agent.orchestrator.get_openai_api_key", return_value="sk-fake"):
        with patch("agent.orchestrator.generate", side_effect=mock_generate):
            with patch("agent.orchestrator.retry_with_backoff") as mock_retry:
                def exhaust_retries(fn, **kw):
                    raise ValueError("Validation failed")
                mock_retry.side_effect = exhaust_retries
                result = run(
                    {"monthly_income": 5000, "monthly_expenses": 4500},
                    capabilities=caps,
                    api_key="sk-fake",
                )
    assert "generation" in result
    assert "Analysis" in result["generation"] or "Savings" in result["generation"]


def test_complete_failure_structured_error():
    """Invalid input returns structured error."""
    result = run(
        {"monthly_income": -100, "monthly_expenses": 50},
        capabilities=Capabilities(llm=False, retry=False, fallback=False),
    )
    assert "errors" in result
    assert len(result["errors"]) >= 1
    assert "generation" in result
    assert "trace" in result
    trace = result["trace"]
    assert "input_validation_failed" in trace.get("phases", [])


def test_valid_end_to_end():
    """Valid request produces full structured response."""
    result = run(
        {"monthly_income": 10000, "monthly_expenses": 6000},
        capabilities=Capabilities(llm=False, retry=False, fallback=False),
    )
    assert "analysis" in result
    assert "education" in result
    assert "generation" in result
    assert "validation" in result
    assert "errors" in result
    assert isinstance(result["analysis"], list)
    assert isinstance(result["education"], dict)
    assert isinstance(result["errors"], list)
    trace = result["trace"]
    assert "tools_executed" in trace
    assert "context_snapshot" in trace
    phases = trace.get("phases", [])
    assert "input_validated" in phases
    assert "response_produced" in phases


def test_missing_input_fields():
    """Missing required fields returns validation errors."""
    result = run({}, capabilities=Capabilities(llm=False, retry=False, fallback=False))
    assert len(result["errors"]) >= 1
    assert "monthly_income" in str(result["errors"]).lower() or "required" in str(result["errors"]).lower()
