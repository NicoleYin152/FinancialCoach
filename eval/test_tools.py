"""Eval tests for tools: tool set correctness for known cases."""

from tools.context import FinancialContext
from tools.registry import TOOL_REGISTRY, run_tools
from tools.schemas import ToolResult


def _ctx(income=5000, expenses=4000, categories=None, allocation=None, savings=None):
    data = {"monthly_income": income, "monthly_expenses": expenses}
    if categories:
        data["expense_categories"] = [{"category": k, "amount": v} for k, v in categories.items()]
    if allocation:
        data["asset_allocation"] = [{"asset_class": k, "allocation_pct": v} for k, v in allocation.items()]
    if savings is not None:
        data["current_savings"] = savings
    return FinancialContext.from_api_input(data)


def test_tool_set_correctness_basic():
    """Basic input: expense_ratio applies, others may not."""
    ctx = _ctx(income=5000, expenses=4600)
    results, executed, _ = run_tools(ctx, selected_tool_names=None)
    assert "input_validation" in executed
    assert "expense_ratio" in executed
    dims = [r.dimension for r in results]
    assert "Savings" in dims or "ExpenseRatio" in dims


def test_tool_set_correctness_with_categories():
    """Expense categories: expense_ratio + expense_concentration apply."""
    ctx = _ctx(
        income=10000,
        expenses=5000,
        categories={"Housing": 3000, "Food": 1000, "Other": 1000},
    )
    results, executed, _ = run_tools(ctx, selected_tool_names=None)
    assert "expense_ratio" in executed
    assert "expense_concentration" in executed
    dims = [r.dimension for r in results]
    assert "ExpenseConcentration" in dims


def test_tool_set_correctness_with_allocation():
    """Asset allocation: expense_ratio + asset_concentration apply."""
    ctx = _ctx(
        income=5000,
        expenses=4000,
        allocation={"Stocks": 90, "Bonds": 10},
    )
    results, executed, _ = run_tools(ctx, selected_tool_names=None)
    assert "expense_ratio" in executed
    assert "asset_concentration" in executed
    dims = [r.dimension for r in results]
    assert "AssetConcentration" in dims


def test_tool_set_correctness_with_savings():
    """Current savings: expense_ratio + liquidity apply."""
    ctx = _ctx(income=5000, expenses=4000, savings=2000)
    results, executed, _ = run_tools(ctx, selected_tool_names=None)
    assert "expense_ratio" in executed
    assert "liquidity" in executed
    dims = [r.dimension for r in results]
    assert "Liquidity" in dims


def test_all_tools_return_tool_result_schema():
    """Every tool returns ToolResult with required fields."""
    ctx = _ctx(income=5000, expenses=4600, allocation={"Stocks": 70}, savings=1000)
    results, _, _ = run_tools(ctx, selected_tool_names=None)
    for r in results:
        assert isinstance(r, ToolResult)
        assert r.tool_name
        assert r.dimension
        assert r.severity in ("low", "medium", "high", "invalid")
        assert r.reason
        assert isinstance(r.metrics, dict)
