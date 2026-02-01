"""Deterministic financial risk rules."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class RuleFinding:
    """A single rule evaluation result."""

    dimension: str
    risk_level: str
    reason: str


def evaluate(input_data: Dict[str, Any]) -> List[RuleFinding]:
    """
    Evaluate financial risk rules on input data.
    Expects monthly_income, monthly_expenses; optional current_savings, risk_tolerance.
    Returns list of RuleFinding. Empty list or invalid-input finding for bad input.
    """
    income = float(input_data.get("monthly_income", 0) or 0)
    expenses = float(input_data.get("monthly_expenses", 0) or 0)

    if income <= 0:
        return [
            RuleFinding(
                dimension="Input",
                risk_level="invalid",
                reason="Zero or negative income",
            )
        ]

    if expenses < 0:
        return [
            RuleFinding(
                dimension="Input",
                risk_level="invalid",
                reason="Negative values not allowed",
            )
        ]

    findings: List[RuleFinding] = []
    savings_rate = (income - expenses) / income if income > 0 else 0
    expense_ratio = expenses / income if income > 0 else 0

    # Savings rate rules
    if savings_rate < 0.10:
        findings.append(
            RuleFinding(
                dimension="Savings",
                risk_level="high",
                reason="Savings rate below 10%",
            )
        )
    elif savings_rate < 0.20:
        findings.append(
            RuleFinding(
                dimension="Savings",
                risk_level="medium",
                reason="Savings rate below 20%",
            )
        )

    # Expense ratio rules
    if expense_ratio > 0.90:
        findings.append(
            RuleFinding(
                dimension="ExpenseRatio",
                risk_level="high",
                reason="Expense ratio above 90%",
            )
        )
    elif expense_ratio > 0.80:
        findings.append(
            RuleFinding(
                dimension="ExpenseRatio",
                risk_level="medium",
                reason="Expense ratio above 80%",
            )
        )

    # Expense concentration rules (when expense_categories provided)
    expense_categories = input_data.get("expense_categories")
    if expense_categories and expenses > 0:
        for cat in expense_categories:
            if isinstance(cat, dict):
                amt = float(cat.get("amount", 0) or 0)
                cname = (cat.get("category") or "").strip()
                if cname and amt > 0:
                    pct = amt / expenses
                    if pct > 0.50:
                        findings.append(
                            RuleFinding(
                                dimension="ExpenseConcentration",
                                risk_level="high",
                                reason=f"Single category ({cname}) exceeds 50% of expenses",
                            )
                        )
                        break
                    elif pct > 0.40:
                        findings.append(
                            RuleFinding(
                                dimension="ExpenseConcentration",
                                risk_level="medium",
                                reason=f"Single category ({cname}) exceeds 40% of expenses",
                            )
                        )
                        break

    # Asset allocation concentration rules (when asset_allocation provided)
    asset_allocation = input_data.get("asset_allocation")
    if asset_allocation:
        for a in asset_allocation:
            if isinstance(a, dict):
                pct = float(a.get("allocation_pct", 0) or 0)
                aclass = (a.get("asset_class") or "").strip()
                if aclass and pct > 0:
                    if pct > 80:
                        findings.append(
                            RuleFinding(
                                dimension="AssetConcentration",
                                risk_level="high",
                                reason=f"Single asset class ({aclass}) exceeds 80%",
                            )
                        )
                        break
                    elif pct > 60:
                        findings.append(
                            RuleFinding(
                                dimension="AssetConcentration",
                                risk_level="medium",
                                reason=f"Single asset class ({aclass}) exceeds 60%",
                            )
                        )
                        break

    return findings
