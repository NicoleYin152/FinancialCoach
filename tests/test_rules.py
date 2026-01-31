"""Tests for tools/rules.py."""

import pytest

from tools.rules import RuleFinding, evaluate


def test_zero_income():
    """Zero income returns invalid finding."""
    result = evaluate({"monthly_income": 0, "monthly_expenses": 100})
    assert len(result) == 1
    assert result[0].dimension == "Input"
    assert result[0].risk_level == "invalid"
    assert "Zero or negative" in result[0].reason


def test_negative_income():
    """Negative income returns invalid finding."""
    result = evaluate({"monthly_income": -100, "monthly_expenses": 50})
    assert len(result) >= 1
    assert result[0].dimension == "Input"
    assert result[0].risk_level == "invalid"


def test_negative_expenses():
    """Negative expenses returns invalid finding."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": -100})
    assert len(result) >= 1
    assert result[0].dimension == "Input"
    assert result[0].risk_level == "invalid"


def test_expenses_greater_than_income():
    """Expenses > income: savings rate negative, high risk on savings."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 1200})
    assert len(result) >= 1
    savings_findings = [f for f in result if f.dimension == "Savings"]
    assert any(f.risk_level == "high" for f in savings_findings)


def test_missing_fields():
    """Missing fields: expenses default to 0; empty dict yields invalid."""
    result = evaluate({"monthly_income": 1000})  # missing expenses -> 0
    # expenses=0, savings_rate=100%, expense_ratio=0 - no rules fire
    assert isinstance(result, list)
    result2 = evaluate({})  # all missing -> income=0 -> invalid
    assert len(result2) >= 1
    assert result2[0].dimension == "Input" and result2[0].risk_level == "invalid"


def test_boundary_savings_rate_exactly_10_percent():
    """Savings rate exactly 10%: no high risk, medium risk (10% < 20%)."""
    # income 1000, expenses 900 -> savings 100, rate 10%
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 900})
    savings = [f for f in result if f.dimension == "Savings"]
    assert not any(f.risk_level == "high" for f in savings)
    assert any(f.risk_level == "medium" for f in savings)


def test_boundary_savings_rate_just_below_10_percent():
    """Savings rate just below 10% -> high risk."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 910})
    savings = [f for f in result if f.dimension == "Savings"]
    assert any(f.risk_level == "high" for f in savings)


def test_boundary_savings_rate_exactly_20_percent():
    """Savings rate exactly 20%: no findings for savings."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 800})
    savings = [f for f in result if f.dimension == "Savings"]
    assert len(savings) == 0


def test_boundary_expense_ratio_exactly_80_percent():
    """Expense ratio exactly 80%: no medium/high expense risk (80% not > 80%)."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 800})
    expense = [f for f in result if f.dimension == "ExpenseRatio"]
    assert len(expense) == 0


def test_boundary_expense_ratio_just_above_80_percent():
    """Expense ratio just above 80% -> medium risk."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 801})
    expense = [f for f in result if f.dimension == "ExpenseRatio"]
    assert any(f.risk_level == "medium" for f in expense)


def test_boundary_expense_ratio_exactly_90_percent():
    """Expense ratio exactly 90%: medium risk (90% > 80%, 90% not > 90%)."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 900})
    expense = [f for f in result if f.dimension == "ExpenseRatio"]
    assert any(f.risk_level == "medium" for f in expense)


def test_boundary_expense_ratio_just_above_90_percent():
    """Expense ratio just above 90% -> high risk."""
    result = evaluate({"monthly_income": 1000, "monthly_expenses": 901})
    expense = [f for f in result if f.dimension == "ExpenseRatio"]
    assert any(f.risk_level == "high" for f in expense)


def test_normal_case_healthy_finances():
    """Healthy finances: no risk findings."""
    result = evaluate({"monthly_income": 10000, "monthly_expenses": 6000})
    invalid = [f for f in result if f.risk_level == "invalid"]
    assert len(invalid) == 0
    # savings rate 40%, expense ratio 60% - both fine
    assert len(result) == 0


def test_normal_case_high_risk():
    """Low savings, high expenses -> multiple findings."""
    result = evaluate({"monthly_income": 5000, "monthly_expenses": 4600})
    assert len(result) >= 1
    # savings 400/5000=8% -> high, expenses 92% -> high
    assert any(f.dimension == "Savings" for f in result)
    assert any(f.dimension == "ExpenseRatio" for f in result)
