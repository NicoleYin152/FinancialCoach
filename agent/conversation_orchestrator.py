"""Conversation orchestrator: multi-turn chat with schema-bound action planning."""

import uuid
from typing import Any, Dict, Optional

from agent.action_executor import execute
from agent.action_planner import select_action
from agent.capabilities import Capabilities
from agent.config import get_openai_api_key
from agent.conversation_store import CONVERSATION_HISTORY
from agent.schemas.action import AgentAction
from agent.schemas.conversation import (
    ConversationState,
    ConversationTurn,
    PendingClarification,
)


def chat(
    message: str,
    conversation_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    capabilities: Capabilities | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """
    Process one chat turn. Returns structured response with conversation_id,
    assistant_message, run_id, analysis, trace, message_type.
    """
    caps = capabilities or Capabilities(llm=False, retry=False, fallback=False, agent=False)
    key = api_key or get_openai_api_key()

    cid = conversation_id or uuid.uuid4().hex
    if cid not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[cid] = ConversationState(conversation_id=cid, turns=[])

    state = CONVERSATION_HISTORY[cid]
    turn_index = len(state.turns)
    state.turns.append(ConversationTurn(role="user", content=message))

    trace: Dict[str, Any] = {
        "planner_decision": "noop",
        "action_taken": "noop",
        "tools_selected": [],
        "tools_executed": [],
        "context_snapshot": {},
        "turn_index": turn_index,
    }
    baseline = getattr(state, "baseline_input", None) or state.last_input_snapshot
    if baseline:
        ctx = _context_snapshot_from_input(baseline)
        trace["context_before"] = ctx

    action: AgentAction = select_action(state, key if caps.agent else None, trace, input_data)

    exec_result = execute(
        action=action,
        state=state,
        input_data=input_data,
        capabilities=caps,
        api_key=key,
        trace=trace,
    )

    assistant_msg = exec_result.get("assistant_message", "")
    msg_type = exec_result.get("message_type", "assistant")
    state.turns.append(
        ConversationTurn(role="assistant", content=assistant_msg, message_type=msg_type)
    )

    run_id = exec_result.get("run_id")
    if run_id:
        state.last_run_id = run_id
        state.last_analysis_summary = _summary_from_analysis(exec_result.get("analysis", []))
        state.pending_clarification = None
        state.clarification_attempt = 0
        trace["clarification_attempt"] = 0
        # Baseline is set only on run_analysis (user submitted category form); never mutated by compare_scenarios
        if action.type == "run_analysis":
            state.baseline_input = input_data or state.baseline_input
            state.last_input_snapshot = input_data or state.last_input_snapshot
            state.last_run_type = "baseline"
            trace["context_after"] = exec_result.get("context_after") or _context_snapshot_from_input(
                input_data
            )
        elif action.type == "compare_scenarios":
            state.last_run_type = "scenario"
            # Do NOT update baseline_input or last_input_snapshot; scenario is temporary
            trace["context_after"] = exec_result.get("context_after")
        else:
            state.last_run_type = None
            state.last_input_snapshot = input_data or state.last_input_snapshot
            trace["context_after"] = exec_result.get("context_after") or _context_snapshot_from_input(
                input_data
            )
    elif action.type == "clarifying_question":
        state.clarification_attempt = getattr(state, "clarification_attempt", 0) + 1
        trace["clarification_attempt"] = state.clarification_attempt
        params = action.parameters or {}
        prev_retry = state.pending_clarification.retry_count if state.pending_clarification else 0
        state.pending_clarification = PendingClarification(
            expected_schema=params.get("expected_schema", "expense_delta"),
            question=params.get("question", "Please specify category and amount."),
            retry_count=prev_retry + 1 if state.pending_clarification else 0,
        )
    elif action.type in ("run_analysis", "compare_scenarios", "explain_previous"):
        state.clarification_attempt = 0
        trace["clarification_attempt"] = 0

    CONVERSATION_HISTORY[cid] = state

    return {
        "conversation_id": cid,
        "assistant_message": assistant_msg,
        "run_id": run_id,
        "analysis": exec_result.get("analysis", []),
        "education": exec_result.get("education", {}),
        "trace": {**trace, **exec_result.get("trace", {})},
        "message_type": msg_type,
        "ui_blocks": exec_result.get("ui_blocks", []),
    }


def _context_snapshot_from_input(input_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build minimal context snapshot from input."""
    if not input_data:
        return {}
    income = input_data.get("monthly_income")
    expenses = input_data.get("monthly_expenses")
    cats = input_data.get("expense_categories") or []
    alloc = input_data.get("asset_allocation") or []
    return {
        "income": float(income or 0),
        "total_expenses": float(expenses or 0) or sum(
            float(c.get("amount", 0) or 0) for c in cats if isinstance(c, dict)
        ),
        "expense_category_count": len(cats),
        "asset_class_count": len(alloc),
    }


def _summary_from_analysis(analysis: list) -> str:
    if not analysis:
        return "No findings."
    parts = [f"{a.get('dimension', '')}: {a.get('risk_level', '')}" for a in analysis[:5]]
    return "; ".join(parts)
