"""Tool result schema. All tools must return exactly this shape."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "invalid"]


class ToolResult(BaseModel):
    """Unified tool result schema. Enforced for all analysis tools."""

    tool_name: str = Field(..., description="Name of the tool that produced this result")
    dimension: str = Field(..., description="Analysis dimension")
    severity: Severity = Field(..., description="Risk severity level")
    reason: str = Field(..., description="Human-readable explanation")
    metrics: dict = Field(default_factory=dict, description="Supporting metrics")
    scenario_impact: Optional[dict] = Field(
        default=None,
        description="When scenario run: baseline vs scenario metric diff",
    )
