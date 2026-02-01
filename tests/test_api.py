"""Tests for api/server.py."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


def test_valid_request():
    """Valid request returns 200 and expected structure."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_income": 8000,
                "monthly_expenses": 5500,
            },
            "capabilities": {"llm": False, "retry": False, "fallback": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert "analysis" in data
    assert "education" in data
    assert "generation" in data
    assert "validation" in data
    assert "errors" in data
    assert "trace" in data


def test_replay_endpoint():
    """Replay endpoint returns stored RunMemory for valid run_id."""
    run_response = client.post(
        "/agent/run",
        json={
            "input": {"monthly_income": 8000, "monthly_expenses": 5500},
            "capabilities": {"llm": False},
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json().get("run_id")
    assert run_id is not None

    replay_response = client.get(f"/agent/replay/{run_id}")
    assert replay_response.status_code == 200
    memory = replay_response.json()
    assert memory["run_id"] == run_id
    assert "tools_selected" in memory
    assert "tool_results" in memory
    assert "context_snapshot" in memory
    assert "timestamp" in memory


def test_chat_endpoint():
    """POST /agent/chat returns conversation_id and assistant_message."""
    response = client.post(
        "/agent/chat",
        json={
            "message": "I make 8000 and spend 5500",
            "input": {"monthly_income": 8000, "monthly_expenses": 5500},
            "capabilities": {"llm": False, "agent": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "assistant_message" in data
    assert data["run_id"] is not None
    assert "trace" in data


def test_chat_endpoint_no_input():
    """POST /agent/chat without input asks for clarification."""
    response = client.post(
        "/agent/chat",
        json={
            "message": "Can you analyze my finances?",
            "capabilities": {"llm": False, "agent": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "assistant_message" in data
    assert data["run_id"] is None
    assert "income" in data["assistant_message"].lower() or "expense" in data["assistant_message"].lower()


def test_replay_endpoint_404():
    """Replay endpoint returns 404 for unknown run_id."""
    response = client.get("/agent/replay/nonexistent_run_id_12345")
    assert response.status_code == 404


def test_missing_required_fields():
    """Missing monthly_income returns 422."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_expenses": 5000,
            },
        },
    )
    assert response.status_code == 422


def test_capability_toggles():
    """Capability toggles affect response (LLM off vs on)."""
    with patch("api.server.get_openai_api_key", return_value=None):
        response_off = client.post(
            "/agent/run",
            json={
                "input": {"monthly_income": 5000, "monthly_expenses": 4000},
                "capabilities": {"llm": True, "retry": False, "fallback": False},
            },
        )
    assert response_off.status_code == 200
    data = response_off.json()
    assert "generation" in data
    assert "analysis" in data


def test_llm_off_behavior():
    """With LLM off, returns deterministic output."""
    response = client.post(
        "/agent/run",
        json={
            "input": {"monthly_income": 5000, "monthly_expenses": 4500},
            "capabilities": {"llm": False, "retry": False, "fallback": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "generation" in data
    assert len(data["generation"]) > 0


def test_negative_income_rejected():
    """Negative income is rejected by Pydantic validation (422)."""
    response = client.post(
        "/agent/run",
        json={
            "input": {"monthly_income": -100, "monthly_expenses": 50},
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 422


def test_expense_categories_instead_of_monthly_expenses():
    """Request with expense_categories (no monthly_expenses) is valid."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_income": 8000,
                "expense_categories": [
                    {"category": "Housing", "amount": 2000},
                    {"category": "Food", "amount": 1000},
                    {"category": "Other", "amount": 500},
                ],
            },
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "education" in data


def test_asset_allocation_valid():
    """Request with asset_allocation summing to 100 is valid."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_income": 8000,
                "monthly_expenses": 5500,
                "asset_allocation": [
                    {"asset_class": "stocks", "allocation_pct": 60},
                    {"asset_class": "bonds", "allocation_pct": 40},
                ],
            },
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data


def test_asset_allocation_invalid_sum_rejected():
    """Asset allocation not summing to 100 is rejected (422)."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_income": 8000,
                "monthly_expenses": 5500,
                "asset_allocation": [
                    {"asset_class": "stocks", "allocation_pct": 60},
                    {"asset_class": "bonds", "allocation_pct": 30},
                ],
            },
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 422


def test_backward_compat_monthly_expenses_only():
    """Legacy request with monthly_income + monthly_expenses only is valid."""
    response = client.post(
        "/agent/run",
        json={
            "input": {
                "monthly_income": 8000,
                "monthly_expenses": 5500,
            },
            "capabilities": {"llm": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "generation" in data
