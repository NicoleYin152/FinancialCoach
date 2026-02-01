"""Input validation tool: basic input sanity checks."""

from tools.context import FinancialContext
from tools.tool_protocol import ToolResult


class InputValidationTool:
    """Analysis tool for input validation. Runs first to catch invalid data."""

    name = "input_validation"
    dimension = "Input"

    def applicable(self, ctx: FinancialContext) -> bool:
        return True

    def run(self, ctx: FinancialContext) -> list[ToolResult]:
        results: list[ToolResult] = []

        if ctx.income <= 0:
            results.append(
                ToolResult(
                    dimension=self.dimension,
                    severity="invalid",
                    reason="Zero or negative income",
                    supporting_metrics={"income": ctx.income},
                )
            )
        if ctx.total_expenses < 0:
            results.append(
                ToolResult(
                    dimension=self.dimension,
                    severity="invalid",
                    reason="Negative values not allowed",
                    supporting_metrics={"total_expenses": ctx.total_expenses},
                )
            )

        return results
