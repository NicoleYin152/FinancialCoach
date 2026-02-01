"""Tool interface. Result schema in tools/schemas.py."""

from typing import Protocol, runtime_checkable

from tools.context import FinancialContext
from tools.schemas import ToolResult

__all__ = ["ToolResult", "AnalysisTool"]


@runtime_checkable
class AnalysisTool(Protocol):
    """Protocol for analysis tools. Each tool declares when it applies and runs independently."""

    name: str
    dimension: str

    def applicable(self, ctx: FinancialContext) -> bool:
        """Return True if this tool should run for the given context."""
        ...

    def run(self, ctx: FinancialContext) -> ToolResult | list[ToolResult]:
        """Run analysis and return one or more ToolResults (from tools.schemas)."""
        ...
