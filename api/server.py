"""FastAPI server for agent run endpoint."""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from agent.capabilities import Capabilities
from agent.config import get_openai_api_key
from agent.conversation_orchestrator import chat
from agent.memory import RUN_HISTORY, RunMemory
from agent.orchestrator import run

app = FastAPI(title="Smart Financial Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExpenseCategory(BaseModel):
    """Expense category with amount."""

    category: str = Field(..., min_length=1)
    amount: float = Field(ge=0)


class AssetAllocation(BaseModel):
    """Asset class with allocation percentage."""

    asset_class: str = Field(..., min_length=1)
    allocation_pct: float = Field(ge=0, le=100)


class AgentInput(BaseModel):
    """Input schema for financial analysis."""

    monthly_income: float = Field(..., gt=0, description="Monthly income (positive)")
    monthly_expenses: Optional[float] = Field(default=None, ge=0, description="Monthly expenses (optional if expense_categories provided)")
    expense_categories: Optional[List[ExpenseCategory]] = Field(default=None)
    asset_allocation: Optional[List[AssetAllocation]] = Field(default=None)
    current_savings: Optional[float] = Field(default=None, ge=0)
    risk_tolerance: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_expenses_or_categories(self) -> "AgentInput":
        has_expenses = self.monthly_expenses is not None
        has_categories = self.expense_categories and len(self.expense_categories) > 0
        if not has_expenses and not has_categories:
            raise ValueError("Either monthly_expenses or expense_categories (non-empty) is required")
        return self

    @model_validator(mode="after")
    def validate_asset_allocation_sum(self) -> "AgentInput":
        if self.asset_allocation and len(self.asset_allocation) > 0:
            total = sum(a.allocation_pct for a in self.asset_allocation)
            if abs(total - 100) > 0.1:
                raise ValueError(f"asset_allocation percentages must sum to 100 (got {total})")
        return self


class CapabilitiesInput(BaseModel):
    """Capability flags from API input."""

    llm: bool = Field(default=False)
    retry: bool = Field(default=False)
    fallback: bool = Field(default=False)
    agent: bool = Field(default=False, description="Enable planner for tool selection")


class AgentRunRequest(BaseModel):
    """Request body for POST /agent/run."""

    input: AgentInput
    capabilities: CapabilitiesInput = Field(default_factory=CapabilitiesInput)
    llm_config: Optional[Dict[str, Any]] = Field(default=None)


class AgentChatRequest(BaseModel):
    """Request body for POST /agent/chat."""

    conversation_id: Optional[str] = Field(default=None, description="Existing conversation or new")
    message: str = Field(..., min_length=1, description="User message")
    input: Optional[AgentInput] = Field(default=None, description="Financial input from editor or context")
    capabilities: CapabilitiesInput = Field(default_factory=CapabilitiesInput)


@app.post("/agent/run")
def agent_run(request: AgentRunRequest) -> Dict[str, Any]:
    """
    Run the financial coaching agent.
    Returns analysis, education, generation, validation, and errors.
    """
    input_dict = request.input.model_dump(exclude_none=True)
    caps_dict = request.capabilities.model_dump()

    api_key = get_openai_api_key()
    capabilities = Capabilities.from_api_input(caps_dict, api_key=api_key)

    result = run(
        input_data=input_dict,
        capabilities=capabilities,
        api_key=api_key,
    )

    return result


@app.post("/agent/chat")
def agent_chat(request: AgentChatRequest) -> Dict[str, Any]:
    """
    Multi-turn conversational agent. Returns assistant_message, run_id, analysis, trace.
    """
    input_dict = request.input.model_dump(exclude_none=True) if request.input else None
    caps_dict = request.capabilities.model_dump()
    api_key = get_openai_api_key()
    capabilities = Capabilities.from_api_input(caps_dict, api_key=api_key)

    result = chat(
        message=request.message,
        conversation_id=request.conversation_id,
        input_data=input_dict,
        capabilities=capabilities,
        api_key=api_key,
    )
    return result


@app.get("/agent/replay/{run_id}")
def agent_replay(run_id: str) -> Dict[str, Any]:
    """
    Debug-only: return stored RunMemory for a given run_id.
    Internal use for replay and debugging.
    """
    if run_id not in RUN_HISTORY:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    memory = RUN_HISTORY[run_id]
    return memory.model_dump()
