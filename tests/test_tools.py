"""Unit tests for analysis tools."""

import pytest

from tools.context import FinancialContext
from tools.expense_ratio_tool import ExpenseRatioTool
from tools.expense_concentration_tool import ExpenseConcentrationTool
from tools.asset_concentration_tool import AssetConcentrationTool
from tools.liquidity_tool import LiquidityTool
from tools.input_validation_tool import InputValidationTool
from tools.registry import TOOL_REGISTRY, run_tools


def _ctx(income=5000, expenses=4000, categories=None, allocation=None, savings=None):
    data = {"monthly_income": income, "monthly_expenses": expenses}
    if categories:
        data["expense_categories"] = [{"category": k, "amount": v} for k, v in categories.items()]
    if allocation:
        data["asset_allocation"] = [{"asset_class": k, "allocation_pct": v} for k, v in allocation.items()]
    if savings is not None:
        data["current_savings"] = savings
    return FinancialContext.from_api_input(data)


def test_expense_ratio_tool_low_savings():
    tool = ExpenseRatioTool()
    ctx = _ctx(income=5000, expenses=4600)
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) >= 1
    savings = [r for r in results if r.dimension == "Savings"]
    assert any(r.severity == "high" for r in savings)


def test_expense_ratio_tool_healthy():
    tool = ExpenseRatioTool()
    ctx = _ctx(income=10000, expenses=6000)
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) == 0


def test_expense_concentration_tool_high():
    tool = ExpenseConcentrationTool()
    ctx = _ctx(income=10000, expenses=5000, categories={"Housing": 3000, "Food": 1000, "Other": 1000})
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) >= 1
    assert results[0].severity == "high"
    assert "50%" in results[0].reason


def test_expense_concentration_tool_diversified():
    tool = ExpenseConcentrationTool()
    ctx = _ctx(income=10000, expenses=5000, categories={"Housing": 1500, "Food": 1000, "Transport": 1000, "Other": 1500})
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) == 0


def test_asset_concentration_tool_high():
    tool = AssetConcentrationTool()
    ctx = _ctx(income=5000, expenses=4000, allocation={"Stocks": 90, "Bonds": 10})
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) >= 1
    assert results[0].severity == "high"
    assert "80%" in results[0].reason


def test_liquidity_tool_low_coverage():
    tool = LiquidityTool()
    ctx = _ctx(income=5000, expenses=4000, savings=2000)
    assert tool.applicable(ctx)
    results = tool.run(ctx)
    assert len(results) >= 1
    assert "months_coverage" in results[0].supporting_metrics


def test_liquidity_tool_not_applicable_without_savings():
    tool = LiquidityTool()
    ctx = _ctx(income=5000, expenses=4000)
    assert not tool.applicable(ctx)


def test_input_validation_tool_invalid_income():
    tool = InputValidationTool()
    ctx = _ctx(income=0, expenses=100)
    results = tool.run(ctx)
    assert len(results) >= 1
    assert results[0].severity == "invalid"


def test_tool_registry_keys():
    assert set(TOOL_REGISTRY.keys()) == {
        "input_validation",
        "expense_ratio",
        "expense_concentration",
        "asset_concentration",
        "liquidity",
    }


def test_run_tools_integration():
    ctx = _ctx(income=5000, expenses=4600)
    results, tools_executed, metrics = run_tools(ctx)
    assert "input_validation" in tools_executed
    assert "expense_ratio" in tools_executed
    assert "savings_rate" in metrics or "expense_ratio" in metrics
    assert len(results) >= 1


def test_run_tools_stops_on_invalid_input():
    ctx = _ctx(income=-100, expenses=50)
    results, tools_executed, metrics = run_tools(ctx)
    assert "input_validation" in tools_executed
    invalid = [r for r in results if r.severity == "invalid"]
    assert len(invalid) >= 1
    assert "expense_ratio" not in tools_executed
