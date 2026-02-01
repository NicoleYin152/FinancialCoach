"""Action executor: deterministic. Strictly follows planner output. No help-text fallback."""

from typing import Any, Dict, List

from agent.capabilities import Capabilities
from agent.memory import RUN_HISTORY
from agent.orchestrator import run
from agent.schemas.action import AgentAction
from agent.schemas.conversation import ConversationState
from agent.schemas.delta import AssetDelta, ExpenseDelta
from tools.context import FinancialContext
from tools.llm import explain_results
from tools.validation import validate_output


CLARIFYING_QUESTIONS = {
    "no_income": "Please enter your monthly income and expense breakdown by category.",
    "no_expenses": "Please enter your monthly expense breakdown by category (category and amount per row).",
    "generic": "Please enter your monthly income and expense breakdown by category.",
}

DEFAULT_NOOP_MESSAGE = "I didn't have enough information to proceed."

# Internal planner reasonings that must not be shown to users
INTERNAL_NOOP_REASONINGS = frozenset({
    "No matching default",
    "No user message",
    "Last turn not user",
    "No turns",
    "LLM output invalid or missing",
    "Unrelated or unclear",
    "Could not parse delta after retry",
})


def execute(
    action: AgentAction,
    state: ConversationState,
    input_data: Dict[str, Any] | None,
    capabilities: Capabilities,
    api_key: str | None,
    trace: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute action deterministically. Only runs what planner decided.
    Returns response dict with assistant_message, run_id, analysis, trace, message_type, ui_blocks.
    """
    trace["action_taken"] = action.type

    if action.type == "clarifying_question":
        question = (action.parameters or {}).get("question") or "Please specify the category and amount (e.g. Transport +1500)."
        expected_schema = (action.parameters or {}).get("expected_schema", "expense_delta")
        ui_blocks = _ui_blocks_for_clarification(expected_schema, input_data)
        return {
            "assistant_message": _safe_validate(question),
            "run_id": None,
            "analysis": [],
            "education": {},
            "trace": trace,
            "action": "clarifying_question",
            "message_type": "clarifying_question",
            "expected_schema": expected_schema,
            "ui_blocks": ui_blocks,
        }

    if action.type == "run_analysis":
        if not input_data or _input_incomplete(input_data):
            msg = _clarifying_message(input_data)
            return {
                "assistant_message": msg,
                "run_id": None,
                "analysis": [],
                "education": {},
                "trace": trace,
                "action": "run_analysis",
                "message_type": "clarifying_question",
                "ui_blocks": [{"type": "editor", "editorType": "financial_input", "value": input_data or {}}],
            }
        result = run(input_data, capabilities, api_key)
        ui_blocks = _ui_blocks_for_analysis(result, input_data)
        return {
            "assistant_message": _safe_validate(result.get("generation", "")),
            "run_id": result.get("run_id"),
            "analysis": result.get("analysis", []),
            "education": result.get("education", {}),
            "trace": {**trace, **result.get("trace", {})},
            "action": "run_analysis",
            "message_type": "assistant",
            "ui_blocks": ui_blocks,
        }

    if action.type == "compare_scenarios":
        return _execute_compare_scenarios(action, state, input_data, capabilities, api_key, trace)

    if action.type == "explain_previous":
        if not state.last_run_id or state.last_run_id not in RUN_HISTORY:
            return {
                "assistant_message": "I don't have analysis results yet. Please run an analysis first.",
                "run_id": state.last_run_id,
                "analysis": [],
                "education": {},
                "trace": trace,
                "action": "explain_previous",
                "message_type": "assistant",
                "ui_blocks": [],
            }
        memory = RUN_HISTORY[state.last_run_id]
        results_str = "\n".join(
            f"- {r['dimension']}: {r.get('severity', 'unknown')} - {r.get('reason', '')}"
            for r in memory.tool_results
        )
        last_user = next((t.content for t in reversed(state.turns) if t.role == "user"), "")
        explanation = explain_results(results_str, last_user, api_key)
        last_run_type = getattr(state, "last_run_type", None)
        prefix = ""
        if last_run_type == "scenario":
            prefix = "This was a scenario comparison (what-if), not your baseline. "
        elif last_run_type == "baseline":
            prefix = "This was your baseline analysis. "
        return {
            "assistant_message": _safe_validate(prefix + explanation),
            "run_id": state.last_run_id,
            "analysis": [
                {"dimension": r["dimension"], "risk_level": r.get("severity"), "reason": r.get("reason", "")}
                for r in memory.tool_results
            ],
            "education": {},
            "trace": trace,
            "action": "explain_previous",
            "message_type": "assistant",
            "ui_blocks": [],
            "last_run_type": last_run_type,
        }

    # noop: never expose internal reasonings; always return a user-safe message
    raw = (action.reasoning or "").strip()
    if raw and raw not in INTERNAL_NOOP_REASONINGS:
        noop_msg = raw
    else:
        noop_msg = DEFAULT_NOOP_MESSAGE
    return {
        "assistant_message": noop_msg,
        "run_id": state.last_run_id,
        "analysis": [],
        "education": {},
        "trace": trace,
        "action": "noop",
        "message_type": "assistant",
        "ui_blocks": [],
    }


def _execute_compare_scenarios(
    action: AgentAction,
    state: ConversationState,
    input_data: Dict[str, Any] | None,
    capabilities: Capabilities,
    api_key: str | None,
    trace: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply delta to immutable baseline only; never use previous scenario as input."""
    baseline_input = state.baseline_input or state.last_input_snapshot or input_data
    if not baseline_input or _input_incomplete(baseline_input):
        return {
            "assistant_message": "I need your baseline financial data first. Please share income and expenses.",
            "run_id": None,
            "analysis": [],
            "education": {},
            "trace": trace,
            "action": "compare_scenarios",
            "message_type": "error",
            "ui_blocks": [{"type": "editor", "editorType": "financial_input", "value": baseline_input or {}}],
        }

    params = action.parameters or {}
    deltas_data = params.get("deltas")
    delta_data = params.get("delta")

    # Multi-delta path (expense deltas only)
    if deltas_data and isinstance(deltas_data, list) and len(deltas_data) > 0:
        try:
            deltas = [ExpenseDelta(**d) for d in deltas_data if isinstance(d, dict) and "monthly_delta" in d]
        except Exception:
            deltas = []
        if not deltas:
            return {
                "assistant_message": "I couldn't parse the changes. Please use format: Category +amount per line (e.g. Transport +1500).",
                "run_id": None,
                "analysis": [],
                "education": {},
                "trace": trace,
                "action": "compare_scenarios",
                "message_type": "error",
                "ui_blocks": [],
            }
        ctx_baseline = FinancialContext.from_api_input(baseline_input)
        ctx_scenario = ctx_baseline.apply_expense_deltas(deltas)
        scenario_label = ", ".join(f"+ {d.category} {d.monthly_delta:+.0f}/mo" for d in deltas)
    elif delta_data:
        try:
            if "monthly_delta" in delta_data:
                delta = ExpenseDelta(**delta_data)
            else:
                delta = AssetDelta(**delta_data)
        except Exception:
            return {
                "assistant_message": "I couldn't parse the change. Please use format: Category +amount (e.g. Transport +1500).",
                "run_id": None,
                "analysis": [],
                "education": {},
                "trace": trace,
                "action": "compare_scenarios",
                "message_type": "error",
                "ui_blocks": [],
            }
        ctx_baseline = FinancialContext.from_api_input(baseline_input)
        if isinstance(delta, ExpenseDelta):
            ctx_scenario = ctx_baseline.apply_expense_delta(delta.category, delta.monthly_delta)
            scenario_label = f"{delta.category} {delta.monthly_delta:+.0f}/mo"
        else:
            ctx_scenario = ctx_baseline.apply_asset_delta(delta.asset_class, delta.allocation_delta_pct)
            scenario_label = f"{delta.asset_class} {delta.allocation_delta_pct:+.0f}%"
    else:
        return {
            "assistant_message": "I couldn't determine the change to model. Please specify category and amount.",
            "run_id": None,
            "analysis": [],
            "education": {},
            "trace": trace,
            "action": "compare_scenarios",
            "message_type": "error",
            "ui_blocks": [],
        }

    scenario_input = ctx_scenario.to_api_input()

    baseline_result = run(baseline_input, capabilities, api_key)
    scenario_result = run(scenario_input, capabilities, api_key)

    trace["compare_baseline_run_id"] = baseline_result.get("run_id")
    trace["compare_scenario_run_id"] = scenario_result.get("run_id")

    base_analysis = {a["dimension"]: a for a in baseline_result.get("analysis", [])}
    scenario_analysis = scenario_result.get("analysis", [])

    analysis_with_diff: List[Dict[str, Any]] = []
    for a in scenario_analysis:
        dim = a.get("dimension", "")
        item = dict(a)
        base_a = base_analysis.get(dim)
        if base_a and base_a.get("risk_level") != a.get("risk_level"):
            item["scenario_impact"] = {
                "baseline_severity": base_a.get("risk_level"),
                "scenario_severity": a.get("risk_level"),
            }
        analysis_with_diff.append(item)

    is_multi_delta = bool(deltas_data and isinstance(deltas_data, list) and len(deltas_data) > 1)
    explanation = _build_scenario_explanation(
        scenario_label, base_analysis, scenario_analysis, api_key, is_multi_delta=is_multi_delta
    )
    ui_blocks = _ui_blocks_for_analysis(
        {"analysis": analysis_with_diff, "education": scenario_result.get("education", {})},
        scenario_input,
    )
    return {
        "assistant_message": _safe_validate(explanation),
        "run_id": scenario_result.get("run_id"),
        "analysis": analysis_with_diff,
        "education": scenario_result.get("education", {}),
        "trace": {**trace, **scenario_result.get("trace", {})},
        "action": "compare_scenarios",
        "message_type": "scenario_result",
        "context_before": ctx_baseline.to_snapshot(),
        "context_after": ctx_scenario.to_snapshot(),
        "ui_blocks": ui_blocks,
    }


def _build_scenario_explanation(
    scenario_label: str,
    base: Dict[str, Dict],
    scenario: List[Dict],
    api_key: str | None,
    is_multi_delta: bool = False,
) -> str:
    """Build diff-aware explanation for scenario result."""
    changes = []
    for a in scenario:
        dim = a.get("dimension", "")
        base_a = base.get(dim)
        if base_a and base_a.get("risk_level") != a.get("risk_level"):
            changes.append(f"{dim}: {base_a.get('risk_level')} → {a.get('risk_level')}")
    if changes:
        if is_multi_delta:
            return f"Scenario analyzed with changes: {scenario_label}. {'; '.join(changes)}. See analysis below for details."
        return f"With {scenario_label}: {'; '.join(changes)}. See analysis below for details."
    if is_multi_delta:
        return f"Scenario analyzed with changes: {scenario_label}. See comparison below."
    return f"Scenario ({scenario_label}) analyzed. See comparison below."


def _ui_blocks_for_analysis(
    result: Dict[str, Any],
    input_data: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    """Build ui_blocks for analysis result: chart + table."""
    blocks: List[Dict[str, Any]] = []
    if not input_data:
        return blocks
    income = float(input_data.get("monthly_income", 0) or 0)
    expenses = float(input_data.get("monthly_expenses", 0) or 0)
    cats = input_data.get("expense_categories") or []
    if not expenses and cats:
        expenses = sum(float(c.get("amount", 0) or 0) for c in cats if isinstance(c, dict))
    savings_rate = (income - expenses) / income if income > 0 else 0
    blocks.append({
        "type": "chart",
        "chartType": "savings_gauge",
        "data": {"savingsRate": savings_rate},
    })
    blocks.append({
        "type": "chart",
        "chartType": "expense_chart",
        "data": {"monthlyIncome": income, "monthlyExpenses": expenses},
    })
    alloc = input_data.get("asset_allocation") or []
    if alloc:
        total = sum(float(a.get("allocation_pct", 0) or 0) for a in alloc if isinstance(a, dict))
        if abs(total - 100) < 0.1:
            blocks.append({
                "type": "chart",
                "chartType": "asset_allocation",
                "data": {"allocation": alloc},
            })
    analysis = result.get("analysis") or []
    if analysis:
        blocks.append({
            "type": "table",
            "schema": "analysis",
            "rows": analysis,
        })
    return blocks


def _ui_blocks_for_clarification(
    expected_schema: str,
    input_data: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    """Build ui_blocks for clarification: category table or delta table. No guessing."""
    blocks: List[Dict[str, Any]] = []
    need_initial_categories = expected_schema == "expense_categories" or not input_data or _input_incomplete(input_data)
    if need_initial_categories:
        blocks.append({
            "type": "editor",
            "editorType": "financial_input",
            "value": {},  # Always empty so user starts fresh; avoids false aggregation from prior input
        })
    elif expected_schema == "expense_delta":
        blocks.append({
            "type": "editor",
            "editorType": "expense_categories",
            "value": input_data.get("expense_categories") if input_data else [],
        })
    elif expected_schema == "asset_change":
        blocks.append({
            "type": "editor",
            "editorType": "asset_allocation",
            "value": input_data.get("asset_allocation") if input_data else [],
        })
    return blocks


def _safe_validate(content: str) -> str:
    """Validate assistant message; return safe fallback if invalid."""
    vr = validate_output(content)
    if vr.valid:
        return content
    return (
        "Based on the analysis, consider reflecting on your financial patterns. "
        "What would you like to explore further?"
    )


def _financial_input_value_for_editor(input_data: Dict[str, Any] | None) -> Dict[str, Any]:
    """Value for financial_input editor: income, expense_categories, current_savings (category table = source of truth)."""
    if not input_data:
        return {}
    return {
        "monthly_income": input_data.get("monthly_income"),
        "monthly_expenses": input_data.get("monthly_expenses"),
        "expense_categories": input_data.get("expense_categories") or [],
        "current_savings": input_data.get("current_savings"),
    }


def _input_incomplete(input_data: Dict[str, Any] | None) -> bool:
    """Category table is source of truth: require income > 0 and non-empty expense_categories."""
    if not input_data:
        return True
    income = input_data.get("monthly_income")
    categories = input_data.get("expense_categories") or []
    has_income = income is not None and float(income or 0) > 0
    cat_total = sum(float(c.get("amount", 0) or 0) for c in categories if isinstance(c, dict))
    has_categories = len(categories) > 0 and cat_total > 0
    return not has_income or not has_categories


def _clarifying_message(input_data: Dict[str, Any] | None) -> str:
    if not input_data:
        return CLARIFYING_QUESTIONS["generic"]
    income = input_data.get("monthly_income")
    expenses = input_data.get("monthly_expenses")
    categories = input_data.get("expense_categories") or []
    has_income = income is not None and float(income or 0) > 0
    has_expenses = (expenses is not None and float(expenses or 0) > 0) or len(categories) > 0
    if not has_income:
        return CLARIFYING_QUESTIONS["no_income"]
    if not has_expenses:
        return CLARIFYING_QUESTIONS["no_expenses"]
    return CLARIFYING_QUESTIONS["generic"]
