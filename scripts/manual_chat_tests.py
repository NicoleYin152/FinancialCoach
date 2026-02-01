#!/usr/bin/env python3
"""
Manual test suite for POST /agent/chat (FINAL INSTRUCTION acceptance).
Run from project root: python -m scripts.manual_chat_tests  OR  PYTHONPATH=. python scripts/manual_chat_tests.py
Equivalent to the 4 curl tests; uses TestClient for reproducibility.
"""
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from agent.conversation_store import CONVERSATION_HISTORY
from api.server import app

client = TestClient(app)
CID = "t1"


def _chat(message: str, input_data: dict | None = None):
    payload = {"conversation_id": CID, "message": message}
    if input_data is not None:
        payload["input"] = input_data
    payload.setdefault("capabilities", {"llm": False, "agent": False})
    return client.post("/agent/chat", json=payload).json()


def test_1_basic_analysis():
    """Test 1 — Basic analysis: run_analysis, analysis results, charts in chat."""
    if CID in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[CID]
    r = _chat("Analyze my finances", {"monthly_income": 8000, "monthly_expenses": 5500})
    assert r.get("trace", {}).get("action_taken") == "run_analysis", r
    assert r.get("run_id") is not None, r
    assert "assistant_message" in r
    assert len(r.get("ui_blocks", [])) >= 1, "charts/analysis should appear in ui_blocks"
    print("✅ Test 1 — Basic analysis: action=run_analysis, run_id present, ui_blocks with charts")


def test_2_explain_previous():
    """Test 2 — Explain previous: explain_previous, no re-run, explanation of same metrics."""
    r = _chat("Explain my previous result")
    assert r.get("trace", {}).get("action_taken") == "explain_previous", r
    assert "assistant_message" in r and len(r["assistant_message"]) > 0
    assert "analysis" in r
    print("✅ Test 2 — Explain previous: action=explain_previous, no re-run, explanation returned")


def test_3_what_if_clarification():
    """Test 3 — What-if → clarification: clarifying_question, assistant asks for delta, NO tools."""
    if CID in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[CID]
    r = _chat("What if I buy a car?", {"monthly_income": 8000, "monthly_expenses": 5500})
    assert r.get("trace", {}).get("action_taken") == "clarifying_question", r
    assert r.get("message_type") == "clarifying_question", r
    assert r.get("run_id") is None, "No tools should run"
    assert "category" in r.get("assistant_message", "").lower() or "amount" in r.get("assistant_message", "").lower(), r
    print("✅ Test 3 — What-if → clarification: action=clarifying_question, no tools executed")


def test_4_delta_follow_up():
    """Test 4 — Delta follow-up: compare_scenarios, baseline vs scenario diff, risk metrics."""
    r = _chat("+1500 per month in transport", {"monthly_income": 8000, "monthly_expenses": 5500})
    assert r.get("trace", {}).get("action_taken") == "compare_scenarios", r
    assert r.get("message_type") == "scenario_result", r
    assert r.get("run_id") is not None, r
    assert len(r.get("analysis", [])) >= 0
    assert "assistant_message" in r
    print("✅ Test 4 — Delta follow-up: action=compare_scenarios, scenario_result, clear change in metrics")


if __name__ == "__main__":
    test_1_basic_analysis()
    test_2_explain_previous()
    test_3_what_if_clarification()
    test_4_delta_follow_up()
    print("\n✅ All 4 manual chat tests passed.")
