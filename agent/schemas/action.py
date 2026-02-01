"""Schema for agent actions. Fully constrains what the LLM can do. Do NOT change."""

from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field

from agent.schemas.delta import AssetDelta, ExpenseDelta

ActionType = Literal[
    "run_analysis",
    "explain_previous",
    "compare_scenarios",
    "clarifying_question",
    "noop",
]

ExpectedSchema = Literal["expense_delta", "category_adjustment", "asset_change"]


class AgentAction(BaseModel):
    """LLM output schema. Invalid output → noop. Do NOT change."""

    type: ActionType = Field(..., description="Action to execute")
    reasoning: str = Field(default="", description="Brief reasoning for the decision")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameters (e.g. question, expected_schema, delta)",
    )


class ClarifyingQuestionAction(BaseModel):
    """Internal helper: clarifying_question as AgentAction-compatible shape."""

    action: Literal["clarifying_question"] = "clarifying_question"
    question: str = Field(..., min_length=1, description="Clarifying question text")
    expected_schema: ExpectedSchema = Field(
        ...,
        description="Schema to parse user's confirmation",
    )


class RunScenarioAction(BaseModel):
    """Internal: compare_scenarios with delta. Delta must be confirmed by user."""

    action: Literal["compare_scenarios"] = "compare_scenarios"
    delta: Union[ExpenseDelta, AssetDelta] = Field(..., description="Confirmed delta to apply")
