"""Unified financial context used by all analysis tools."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class FinancialContext(BaseModel):
    """Normalized context object used by all tools. Populated once in orchestrator."""

    income: float = Field(..., description="Monthly income (may be invalid)")
    total_expenses: float = Field(..., ge=0, description="Total monthly expenses")
    expense_categories: Dict[str, float] = Field(
        default_factory=dict,
        description="Category name -> amount mapping",
    )
    asset_allocation: Dict[str, float] = Field(
        default_factory=dict,
        description="Asset class -> allocation percentage mapping",
    )
    current_savings: Optional[float] = Field(default=None, ge=0)

    derived_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Computed metrics (savings_rate, expense_ratio, etc.)",
    )

    @classmethod
    def from_api_input(cls, data: dict) -> "FinancialContext":
        """Build FinancialContext from API input dict."""
        income = float(data.get("monthly_income", 0) or 0)
        expenses = float(data.get("monthly_expenses", 0) or 0)

        if expenses == 0 and data.get("expense_categories"):
            cats = data["expense_categories"]
            expenses = sum(
                float(c.get("amount", 0) or 0)
                for c in cats
                if isinstance(c, dict)
            )

        expense_categories: Dict[str, float] = {}
        if data.get("expense_categories"):
            for c in data["expense_categories"]:
                if isinstance(c, dict):
                    name = (c.get("category") or "").strip()
                    amt = float(c.get("amount", 0) or 0)
                    if name and amt > 0:
                        expense_categories[name] = amt

        asset_allocation: Dict[str, float] = {}
        if data.get("asset_allocation"):
            for a in data["asset_allocation"]:
                if isinstance(a, dict):
                    ac = (a.get("asset_class") or "").strip()
                    pct = float(a.get("allocation_pct", 0) or 0)
                    if ac and pct > 0:
                        asset_allocation[ac] = pct

        current_savings = data.get("current_savings")
        if current_savings is not None:
            current_savings = float(current_savings) if current_savings else None

        savings_rate = (income - expenses) / income if income > 0 else 0.0
        expense_ratio = expenses / income if income > 0 else 0.0

        months_coverage = 0.0
        if current_savings is not None and current_savings > 0 and expenses > 0:
            months_coverage = current_savings / expenses

        derived = {
            "savings_rate": savings_rate,
            "expense_ratio": expense_ratio,
            "months_coverage": months_coverage,
        }

        return cls(
            income=income,
            total_expenses=expenses,
            expense_categories=expense_categories,
            asset_allocation=asset_allocation,
            current_savings=current_savings,
            derived_metrics=derived,
        )

    def to_snapshot(self) -> dict:
        """Serialize for trace/replay (non-PII friendly)."""
        return {
            "income": self.income,
            "total_expenses": self.total_expenses,
            "expense_category_count": len(self.expense_categories),
            "asset_class_count": len(self.asset_allocation),
            "derived_metrics": self.derived_metrics.copy(),
        }
