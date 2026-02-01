"""Expense ratio tool: savings rate, expense ratio, liquidity impact."""

from tools.context import FinancialContext
from tools.tool_protocol import ToolResult


class ExpenseRatioTool:
    """Analysis tool for savings rate and expense ratio."""

    name = "expense_ratio"
    dimension = "ExpenseRatio"

    def applicable(self, ctx: FinancialContext) -> bool:
        return ctx.income > 0 and ctx.total_expenses >= 0

    def run(self, ctx: FinancialContext) -> list[ToolResult]:
        results: list[ToolResult] = []
        savings_rate = ctx.derived_metrics.get("savings_rate", 0.0)
        expense_ratio = ctx.derived_metrics.get("expense_ratio", 0.0)

        # Savings rate findings
        if savings_rate < 0.10:
            results.append(
                ToolResult(
                    dimension="Savings",
                    severity="high",
                    reason="Savings rate below 10%",
                    supporting_metrics={"savings_rate": savings_rate},
                )
            )
        elif savings_rate < 0.20:
            results.append(
                ToolResult(
                    dimension="Savings",
                    severity="medium",
                    reason="Savings rate below 20%",
                    supporting_metrics={"savings_rate": savings_rate},
                )
            )

        # Expense ratio findings
        if expense_ratio > 0.90:
            results.append(
                ToolResult(
                    dimension=self.dimension,
                    severity="high",
                    reason="Expense ratio above 90%",
                    supporting_metrics={"expense_ratio": expense_ratio},
                )
            )
        elif expense_ratio > 0.80:
            results.append(
                ToolResult(
                    dimension=self.dimension,
                    severity="medium",
                    reason="Expense ratio above 80%",
                    supporting_metrics={"expense_ratio": expense_ratio},
                )
            )

        return results
