"""Liquidity tool: months of coverage, shock simulation (−20% income)."""

from tools.context import FinancialContext
from tools.schemas import ToolResult


class LiquidityTool:
    """Analysis tool for liquidity and shock resilience."""

    name = "liquidity"
    dimension = "Liquidity"

    def applicable(self, ctx: FinancialContext) -> bool:
        return (
            ctx.current_savings is not None
            and ctx.current_savings > 0
            and ctx.total_expenses > 0
        )

    def run(self, ctx: FinancialContext) -> list[ToolResult]:
        results: list[ToolResult] = []
        months_coverage = ctx.derived_metrics.get("months_coverage", 0.0)
        savings = ctx.current_savings or 0
        expenses = ctx.total_expenses
        income = ctx.income

        # Shock simulation: −20% income → new income, same expenses
        shock_income = income * 0.80
        shock_deficit = max(0, expenses - shock_income)
        shock_months_coverage = months_coverage
        if shock_deficit > 0 and savings > 0:
            shock_months_coverage = savings / shock_deficit

        # Months of coverage thresholds
        if months_coverage < 1:
            results.append(
                ToolResult(
                    tool_name=self.name,
                    dimension=self.dimension,
                    severity="high",
                    reason="Less than 1 month of expense coverage in savings",
                    metrics={
                        "months_coverage": months_coverage,
                        "current_savings": savings,
                        "monthly_expenses": expenses,
                        "shock_income_20pct_drop": shock_income,
                        "shock_months_coverage": shock_months_coverage,
                    },
                )
            )
        elif months_coverage < 3:
            results.append(
                ToolResult(
                    tool_name=self.name,
                    dimension=self.dimension,
                    severity="medium",
                    reason="Less than 3 months of expense coverage",
                    metrics={
                        "months_coverage": months_coverage,
                        "current_savings": savings,
                        "monthly_expenses": expenses,
                        "shock_income_20pct_drop": shock_income,
                        "shock_months_coverage": shock_months_coverage,
                    },
                )
            )

        return results
