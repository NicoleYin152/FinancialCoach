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

    def to_api_input(self) -> dict:
        """Convert back to API input format for scenario construction."""
        data = {
            "monthly_income": self.income,
            "monthly_expenses": self.total_expenses,
            "expense_categories": [{"category": k, "amount": v} for k, v in self.expense_categories.items()],
            "asset_allocation": [{"asset_class": k, "allocation_pct": v} for k, v in self.asset_allocation.items()],
        }
        if self.current_savings is not None:
            data["current_savings"] = self.current_savings
        return data

    def apply_expense_delta(self, category: str, monthly_delta: float) -> "FinancialContext":
        """Clone and apply expense delta. Returns new context."""
        cats = dict(self.expense_categories)
        if not cats and self.total_expenses > 0:
            cats["Other"] = self.total_expenses
        cats[category] = cats.get(category, 0) + monthly_delta
        cats = {k: v for k, v in cats.items() if v > 0}
        new_expenses = sum(cats.values())
        income = self.income
        savings_rate = (income - new_expenses) / income if income > 0 else 0.0
        expense_ratio = new_expenses / income if income > 0 else 0.0
        months = 0.0
        if self.current_savings and self.current_savings > 0 and new_expenses > 0:
            months = self.current_savings / new_expenses
        return FinancialContext(
            income=income,
            total_expenses=new_expenses,
            expense_categories=cats,
            asset_allocation=dict(self.asset_allocation),
            current_savings=self.current_savings,
            derived_metrics={
                "savings_rate": savings_rate,
                "expense_ratio": expense_ratio,
                "months_coverage": months,
            },
        )

    def apply_asset_delta(self, asset_class: str, allocation_delta_pct: float) -> "FinancialContext":
        """Clone and apply asset allocation delta. Redistributes to keep 100%."""
        alloc = dict(self.asset_allocation)
        alloc[asset_class] = alloc.get(asset_class, 0) + allocation_delta_pct
        alloc = {k: v for k, v in alloc.items() if v > 0}
        total = sum(alloc.values())
        if abs(total - 100) > 0.1 and alloc:
            scale = 100 / total
            alloc = {k: v * scale for k, v in alloc.items()}
        return FinancialContext(
            income=self.income,
            total_expenses=self.total_expenses,
            expense_categories=dict(self.expense_categories),
            asset_allocation=alloc,
            current_savings=self.current_savings,
            derived_metrics=dict(self.derived_metrics),
        )
