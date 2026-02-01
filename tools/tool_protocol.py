"""Tool interface and result types."""

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol, runtime_checkable

from tools.context import FinancialContext


@dataclass
class ToolResult:
    """Structured output from an analysis tool."""

    dimension: str
    severity: str  # high, medium, invalid, or ok
    reason: str
    supporting_metrics: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AnalysisTool(Protocol):
    """Protocol for analysis tools. Each tool declares when it applies and runs independently."""

    name: str
    dimension: str

    def applicable(self, ctx: FinancialContext) -> bool:
        """Return True if this tool should run for the given context."""
        ...

    def run(self, ctx: FinancialContext) -> ToolResult | list[ToolResult]:
        """Run analysis and return one or more ToolResults."""
        ...
