"""Planner output schema. JSON only, no free-text."""

from typing import List, Literal

from pydantic import BaseModel, Field

ToolName = Literal[
    "expense_ratio",
    "expense_concentration",
    "asset_concentration",
    "liquidity",
]


class ToolSelection(BaseModel):
    """Schema for planner tool selection. Must be valid JSON."""

    tools: List[ToolName] = Field(
        description="List of tools to execute. Must be valid tool names.",
    )
