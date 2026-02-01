"""In-memory run history for replay and debug. Not persistence."""

import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RunMemory(BaseModel):
    """Lightweight memory for a single agent run. Used for replay/debug only."""

    run_id: str = Field(..., description="Unique run identifier")
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of financial context at run time",
    )
    tools_selected: List[str] = Field(
        default_factory=list,
        description="Tools selected by planner (or fallback)",
    )
    tool_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Serialized tool results",
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp when run completed",
    )


RUN_HISTORY: Dict[str, RunMemory] = {}
