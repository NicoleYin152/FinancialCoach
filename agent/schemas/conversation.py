"""Conversation state model for multi-turn chat."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["user", "assistant", "system"]


class ConversationTurn(BaseModel):
    """A single message in the conversation."""

    role: Role = Field(..., description="Sender role")
    content: str = Field(..., description="Message content")
    message_type: Optional[Literal["assistant", "clarifying_question", "scenario_result", "error"]] = (
        Field(default="assistant", description="For assistant: display type")
    )


class PendingClarification(BaseModel):
    """Tracks when we asked a clarifying question and await user confirmation."""

    expected_schema: Literal["expense_delta", "category_adjustment", "asset_change", "expense_categories"]
    question: str = Field(..., description="Question we asked")
    retry_count: int = Field(default=0, ge=0, le=1, description="Times we re-asked after parse failure")


RunType = Literal["baseline", "scenario"]


class ConversationState(BaseModel):
    """State passed into the action planner. Baseline is immutable; scenarios apply deltas to it."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    turns: List[ConversationTurn] = Field(
        default_factory=list,
        description="Message history",
    )
    last_run_id: Optional[str] = Field(
        default=None,
        description="run_id from most recent analysis (baseline or scenario)",
    )
    last_analysis_summary: Optional[str] = Field(
        default=None,
        description="Brief summary of last tool results",
    )
    last_run_type: Optional[RunType] = Field(
        default=None,
        description="Whether last run was baseline analysis or scenario comparison",
    )
    baseline_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Immutable baseline financial input; set once when user submits category form; used for all scenario deltas",
    )
    last_input_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Financial input used in last baseline run (same as baseline_input after run_analysis)",
    )
    pending_clarification: Optional[PendingClarification] = Field(
        default=None,
        description="When awaiting delta confirmation",
    )
    clarification_attempt: int = Field(
        default=0,
        ge=0,
        description="Number of clarification_question actions sent this unresolved-intent cycle; resets on run_analysis/compare_scenarios/explain_previous.",
    )
