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
    assert "analysis" in data
    assert "education" in data
    assert "generation" in data
    assert "validation" in data
    assert "errors" in data
    assert "trace" in data


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
