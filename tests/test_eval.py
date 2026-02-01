"""Eval framework tests: planner and tool output evaluation."""

from tools.context import FinancialContext
from tools.registry import run_tools
from agent.planner import select_tools
from agent.orchestrator import run
from agent.capabilities import Capabilities
from eval.cases import EvalCase


def build_context(case: EvalCase) -> FinancialContext:
    """Build FinancialContext from eval case input."""
    data = dict(case.input)
    if not data.get("monthly_expenses") and data.get("expense_categories"):
        total = sum(
            float(c.get("amount", 0) or 0)
            for c in data["expense_categories"]
            if isinstance(c, dict)
        )
        data["monthly_expenses"] = total
    return FinancialContext.from_api_input(data)


# Eval cases per plan
EVAL_CASES = [
    EvalCase(
        name="missing_categories_basic",
        input={"monthly_income": 8000, "monthly_expenses": 5500},
        expected_tools=["expense_ratio"],
        expected_dimensions=[],  # Healthy case: 31% savings, 69% expense ratio - no findings
    ),
    EvalCase(
        name="partial_asset_allocation",
        input={
            "monthly_income": 10000,
            "monthly_expenses": 6000,
            "asset_allocation": [
                {"asset_class": "stocks", "allocation_pct": 90},
                {"asset_class": "bonds", "allocation_pct": 10},
            ],
        },
        expected_tools=["expense_ratio", "asset_concentration"],
        expected_dimensions=["AssetConcentration"],
    ),
    EvalCase(
        name="extreme_expense_concentration",
        input={
            "monthly_income": 10000,
            "monthly_expenses": 5000,
            "expense_categories": [
                {"category": "Housing", "amount": 3000},
                {"category": "Food", "amount": 1000},
                {"category": "Other", "amount": 1000},
            ],
        },
        expected_tools=["expense_ratio", "expense_concentration"],
        expected_dimensions=["ExpenseConcentration"],
    ),
    EvalCase(
        name="high_risk_savings",
        input={"monthly_income": 5000, "monthly_expenses": 4600},
        expected_tools=["expense_ratio"],
        expected_dimensions=["Savings", "ExpenseRatio"],
    ),
    EvalCase(
        name="liquidity_low_coverage",
        input={
            "monthly_income": 5000,
            "monthly_expenses": 4000,
            "current_savings": 2000,
        },
        expected_tools=["expense_ratio", "liquidity"],
        expected_dimensions=["Liquidity"],
    ),
]


def test_planner_tool_selection():
    """Planner (when disabled) returns all tools; tools selected include expected."""
    for case in EVAL_CASES:
        ctx = build_context(case)
        trace = {}
        select_tools(ctx, capabilities_agent=False, api_key=None, trace=trace)
        tools_selected = trace.get("tools_selected", [])
        for t in case.expected_tools:
            if t != "input_validation":
                assert t in tools_selected, f"Case {case.name}: expected {t} in tools_selected"


def test_tool_outputs():
    """Tool outputs contain expected dimensions for each eval case."""
    for case in EVAL_CASES:
        result = run(
            case.input,
            capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
        )
        dims = [a["dimension"] for a in result.get("analysis", [])]
        for d in case.expected_dimensions:
            assert d in dims, f"Case {case.name}: expected dimension {d} in {dims}"


def test_tool_output_fallback_behavior():
    """Invalid input does not crash; validation fails before tools run."""
    result = run(
        {"monthly_income": -100, "monthly_expenses": 50},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    assert "errors" in result
    assert len(result["errors"]) >= 1
    assert "trace" in result
    assert result["trace"]["phases"][0] == "input_validation_failed"


def test_orchestrator_trace_schema():
    """Trace includes required fields for replay and eval."""
    result = run(
        {"monthly_income": 8000, "monthly_expenses": 5500},
        capabilities=Capabilities(llm=False, retry=False, fallback=False, agent=False),
    )
    trace = result["trace"]
    assert "planner_used" in trace
    assert "planner_status" in trace
    assert "tools_selected" in trace
    assert "tools_executed" in trace
    assert "context_snapshot" in trace
