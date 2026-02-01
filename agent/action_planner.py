"""Action planner: LLM-driven, schema-bound. Invalid output → noop. No silent fallback."""

from typing import Any, Dict

from agent.delta_parser import parse_user_confirmation
from agent.schemas.action import AgentAction
from agent.schemas.conversation import ConversationState, PendingClarification


# Ambiguous intents: financial change mentioned but no structured delta
AMBIGUOUS_INTENT_KEYWORDS = [
    "buy a car",
    "reduce spending",
    "add expense",
    "cut costs",
    "what if i spend",
    "upgrade lifestyle",
    "buy car",
    "new car",
    "reduce expense",
    "add transport",
    "spend more",
    "spend less",
    "cut expense",
    "increase spending",
    "what if",
]


def _has_ambiguous_intent(msg: str) -> bool:
    """Detect if user intent implies financial change but is ambiguous (no delta)."""
    m = msg.lower()
    return any(kw in m for kw in AMBIGUOUS_INTENT_KEYWORDS)


def _has_structured_delta(msg: str) -> bool:
    """Heuristic: user message contains numbers that could be a delta."""
    import re
    return bool(re.search(r"[\d]+", msg)) and ("+" in msg or "-" in msg or "$" in msg or "%" in msg)


def select_action(
    state: ConversationState,
    api_key: str | None,
    trace: Dict[str, Any],
) -> AgentAction:
    """
    Select next action from conversation state. Always returns valid AgentAction.
    LLM is called when api_key is set; invalid LLM output → noop (no heuristic fallback).
    Ambiguous financial intent with no delta → clarifying_question (no tools).
    """
    trace["action_planner_used"] = bool(api_key and api_key.strip())
    clarification_attempt = getattr(state, "clarification_attempt", 0) or 0
    trace["clarification_attempt"] = clarification_attempt

    if not state.turns:
        trace["action_planner_status"] = "skipped"
        return AgentAction(type="noop", reasoning="No user message", parameters={})

    last = state.turns[-1]
    if last.role != "user":
        trace["action_planner_status"] = "skipped"
        return AgentAction(type="noop", reasoning="Last turn not user", parameters={})

    msg = last.content.strip()

    # Follow-up: we asked clarifying question, await confirmation
    if state.pending_clarification:
        delta = parse_user_confirmation(msg, state.pending_clarification.expected_schema)
        if delta is not None:
            trace["action_planner_status"] = "confirmation_parsed"
            trace["planner_decision"] = "compare_scenarios"
            return AgentAction(
                type="compare_scenarios",
                reasoning="User confirmed delta",
                parameters={"delta": delta.model_dump()},
            )
        if state.pending_clarification.retry_count < 1:
            if clarification_attempt >= 2:
                trace["action_planner_status"] = "clarification_limit"
                trace["planner_decision"] = "noop_due_to_clarification_limit"
                trace["clarification_attempt"] = 3
                return AgentAction(
                    type="noop",
                    reasoning="I couldn't get enough information to proceed with an analysis or scenario comparison.",
                    parameters={},
                )
            trace["action_planner_status"] = "confirmation_retry"
            trace["planner_decision"] = "clarifying_question"
            return AgentAction(
                type="clarifying_question",
                reasoning="Retry parsing delta",
                parameters={
                    "question": _retry_clarification(state.pending_clarification),
                    "expected_schema": state.pending_clarification.expected_schema,
                },
            )
        if clarification_attempt >= 2:
            trace["action_planner_status"] = "clarification_limit"
            trace["planner_decision"] = "noop_due_to_clarification_limit"
            trace["clarification_attempt"] = 3
            return AgentAction(
                type="noop",
                reasoning="I couldn't get enough information to proceed with an analysis or scenario comparison.",
                parameters={},
            )
        trace["action_planner_status"] = "confirmation_failed_noop"
        trace["planner_decision"] = "noop"
        return AgentAction(type="noop", reasoning="Could not parse delta after retry", parameters={})

    # Ambiguous financial intent → clarifying_question (NEVER run tools); cap at 2 attempts
    if _has_ambiguous_intent(msg) and not _has_structured_delta(msg):
        if clarification_attempt >= 2:
            trace["action_planner_status"] = "clarification_limit"
            trace["planner_decision"] = "noop_due_to_clarification_limit"
            trace["clarification_attempt"] = 3
            return AgentAction(
                type="noop",
                reasoning="I couldn't get enough information to proceed with an analysis or scenario comparison.",
                parameters={},
            )
        trace["action_planner_status"] = "ambiguous_intent"
        trace["planner_decision"] = "clarifying_question"
        return AgentAction(
            type="clarifying_question",
            reasoning="User intent implies financial change but no structured delta",
            parameters={
                "question": _build_clarifying_question(msg),
                "expected_schema": "expense_delta",
            },
        )

    # LLM path: always call when api_key set; invalid output → noop only
    if api_key and api_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = _build_planner_prompt(state)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            raw = response.choices[0].message.content
            if raw and raw.strip():
                json_str = _extract_json(raw.strip())
                parsed = AgentAction.model_validate_json(json_str)
                # Normalize: ensure type is one of the 5 allowed
                if parsed.type in ("run_analysis", "explain_previous", "compare_scenarios", "clarifying_question", "noop"):
                    trace["action_planner_status"] = "valid"
                    trace["planner_decision"] = parsed.type
                    return parsed
        except Exception:
            pass
        # LLM failed or invalid: return noop only (no silent heuristic fallback)
        trace["action_planner_status"] = "invalid_or_error"
        trace["planner_decision"] = "noop"
        return AgentAction(type="noop", reasoning="LLM output invalid or missing", parameters={})

    # LLM disabled: deterministic fallback only
    trace["action_planner_status"] = "fallback_no_llm"
    return _default_action(state, trace)


def _build_clarifying_question(msg: str) -> str:
    """Build clarifying question for ambiguous intent."""
    return (
        "Should I model this as a change to your monthly expenses? "
        "For example: \"+$1500/month in Transport\" or \"-$200 in Dining\". "
        "Please specify the category and amount."
    )


def _retry_clarification(pc: PendingClarification) -> str:
    """Retry message when first confirmation parse failed."""
    if pc.expected_schema in ("expense_delta", "category_adjustment"):
        return "I couldn't parse that. Please use format: Category +amount or Category -amount (e.g. Transport +1500)."
    return "I couldn't parse that. Please use format: AssetClass +/-percentage (e.g. Stocks -10)."


def _build_planner_prompt(state: ConversationState) -> str:
    """Build prompt for LLM: available actions, tool descriptions, context, previous analysis."""
    tool_desc = (
        "Tools used by the agent: input_validation, expense_ratio, expense_concentration, "
        "asset_concentration, liquidity. run_analysis runs all tools on current financial input. "
        "explain_previous uses stored results only. compare_scenarios runs tools on baseline vs scenario (needs delta)."
    )
    has_previous = "Yes" if (state.last_run_id and state.last_analysis_summary) else "No"
    context_summary = "None"
    if state.last_input_snapshot:
        inc = state.last_input_snapshot.get("monthly_income")
        exp = state.last_input_snapshot.get("monthly_expenses")
        context_summary = f"income={inc}, expenses={exp} (from last run)"
    elif state.turns:
        context_summary = "User has not yet provided full financial input"

    parts = [
        "You are a financial analysis agent. Your job is to decide the next action.",
        "",
        "Available actions (return exactly one):",
        "- run_analysis: when user wants to analyze finances (income/expenses given or requested)",
        "- explain_previous: when user asks about earlier results (e.g. explain, why, what does that mean)",
        "- compare_scenarios: when user proposes a concrete change with numbers (e.g. Transport +1500)",
        "- clarifying_question: when required data is missing or intent is ambiguous (e.g. 'what if I buy a car' with no numbers)",
        "- noop: only if user message is unrelated to finance",
        "",
        tool_desc,
        "",
        f"Current financial context summary: {context_summary}",
        f"Previous analysis exists: {has_previous}",
    ]
    if state.last_analysis_summary:
        parts.append(f"Last analysis: {state.last_analysis_summary[:200]}")
    parts.append("")
    parts.append("You must return valid JSON matching this schema only (no other text):")
    parts.append('{"type": "<one of run_analysis | explain_previous | compare_scenarios | clarifying_question | noop>", "reasoning": "<brief reason>", "parameters": {}}')
    parts.append("For clarifying_question, set parameters to {\"question\": \"<your question>\", \"expected_schema\": \"expense_delta\"}.")
    parts.append("NEVER guess deltas. If unclear, use clarifying_question.")
    parts.append("")
    parts.append("Latest user message:")
    if state.turns:
        parts.append(state.turns[-1].content)
    return "\n".join(parts)


def _extract_json(raw: str) -> str:
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return text[start:end]
    return text


def _default_action(state: ConversationState, trace: Dict[str, Any]) -> AgentAction:
    """Deterministic fallback only when LLM is disabled."""
    if not state.turns:
        return AgentAction(type="noop", reasoning="No turns", parameters={})

    last = state.turns[-1]
    if last.role != "user":
        return AgentAction(type="noop", reasoning="Last not user", parameters={})

    msg = last.content.lower().strip()

    if not state.last_run_id:
        if any(kw in msg for kw in ["income", "expense", "savings", "analyze", "help", "?", "make", "spend"]):
            trace["planner_decision"] = "run_analysis"
            return AgentAction(type="run_analysis", reasoning="Default: run analysis", parameters={})
        if any(kw in msg for kw in ["what if", "compare", "scenario"]) and _has_structured_delta(last.content):
            trace["planner_decision"] = "compare_scenarios"
            return AgentAction(type="compare_scenarios", reasoning="Default: scenario with delta", parameters={})
        trace["planner_decision"] = "noop"
        return AgentAction(type="noop", reasoning="Unrelated or unclear", parameters={})

    if any(kw in msg for kw in ["why", "explain", "mean", "what does"]):
        trace["planner_decision"] = "explain_previous"
        return AgentAction(type="explain_previous", reasoning="Default: explain previous", parameters={})
    if any(kw in msg for kw in ["what if", "compare", "scenario"]) and _has_structured_delta(last.content):
        trace["planner_decision"] = "compare_scenarios"
        return AgentAction(type="compare_scenarios", reasoning="Default: scenario", parameters={})
    if any(kw in msg for kw in ["update", "change", "new", "different"]):
        trace["planner_decision"] = "run_analysis"
        return AgentAction(type="run_analysis", reasoning="Default: re-run analysis", parameters={})

    trace["planner_decision"] = "noop"
    return AgentAction(type="noop", reasoning="No matching default", parameters={})
