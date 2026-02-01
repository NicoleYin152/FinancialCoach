"""Expense concentration tool: category dominance, structural rigidity."""

from tools.context import FinancialContext
from tools.schemas import ToolResult


class ExpenseConcentrationTool:
    """Analysis tool for expense category concentration."""

    name = "expense_concentration"
    dimension = "ExpenseConcentration"

    def applicable(self, ctx: FinancialContext) -> bool:
        return bool(ctx.expense_categories) and ctx.total_expenses > 0

    def run(self, ctx: FinancialContext) -> list[ToolResult]:
        results: list[ToolResult] = []
        total = ctx.total_expenses

        for cat_name, amt in ctx.expense_categories.items():
            if amt <= 0:
                continue
            pct = amt / total
            if pct > 0.50:
                results.append(
                    ToolResult(
                        tool_name=self.name,
                        dimension=self.dimension,
                        severity="high",
                        reason=f"Single category ({cat_name}) exceeds 50% of expenses",
                        metrics={
                            "largest_category_pct": pct,
                            "dominant_category": cat_name,
                            "amount": amt,
                        },
                    )
                )
                break
            elif pct > 0.40:
                results.append(
                    ToolResult(
                        tool_name=self.name,
                        dimension=self.dimension,
                        severity="medium",
                        reason=f"Single category ({cat_name}) exceeds 40% of expenses",
                        metrics={
                            "largest_category_pct": pct,
                            "dominant_category": cat_name,
                            "amount": amt,
                        },
                    )
                )
                break

        return results
