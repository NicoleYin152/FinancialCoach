"""Eval case schema for planner and tool output evaluation."""

from typing import Dict, List

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """Schema for eval cases. Used for planner and tool output evaluation."""

    name: str = Field(..., description="Case name for identification")
    input: Dict = Field(..., description="API input dict (monthly_income, monthly_expenses, etc.)")
    expected_tools: List[str] = Field(
        default_factory=list,
        description="Tools that should run for this input",
    )
    expected_dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensions that should appear in analysis output",
    )
