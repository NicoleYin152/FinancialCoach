"""Delta schemas for scenario modeling. Schema-bound user confirmation."""

from typing import Literal, Union

from pydantic import BaseModel, Field


class ExpenseDelta(BaseModel):
    """Expense category change for scenario modeling."""

    category: str = Field(..., min_length=1, description="Expense category name")
    monthly_delta: float = Field(..., description="Monthly change in dollars (positive or negative)")


class AssetDelta(BaseModel):
    """Asset allocation change for scenario modeling."""

    asset_class: str = Field(..., min_length=1, description="Asset class name")
    allocation_delta_pct: float = Field(
        ...,
        description="Allocation change in percentage points (e.g. -10 means reduce by 10pp)",
    )


DeltaType = Union[ExpenseDelta, AssetDelta]
ExpectedSchema = Literal["expense_delta", "category_adjustment", "asset_change"]
