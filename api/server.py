"""FastAPI server for agent run endpoint."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.capabilities import Capabilities
from agent.config import get_openai_api_key
from agent.orchestrator import run

app = FastAPI(title="Smart Financial Coach API")


class AgentInput(BaseModel):
    """Input schema for financial analysis."""

    monthly_income: float = Field(..., gt=0, description="Monthly income (positive)")
    monthly_expenses: float = Field(..., ge=0, description="Monthly expenses (non-negative)")
    current_savings: Optional[float] = Field(default=None, ge=0)
    risk_tolerance: Optional[str] = Field(default=None)


class CapabilitiesInput(BaseModel):
    """Capability flags from API input."""

    llm: bool = Field(default=False)
    retry: bool = Field(default=False)
    fallback: bool = Field(default=False)


class AgentRunRequest(BaseModel):
    """Request body for POST /agent/run."""

    input: AgentInput
    capabilities: CapabilitiesInput = Field(default_factory=CapabilitiesInput)
    llm_config: Optional[Dict[str, Any]] = Field(default=None)


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
