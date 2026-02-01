"""Planner: LLM-driven tool selection. Schema-constrained, fallback mandatory."""

from typing import Any, Dict, List

from agent.schemas.planner import ToolSelection
from tools.context import FinancialContext
from tools.registry import PLANNER_TOOL_NAMES, TOOL_REGISTRY


PLANNER_SYSTEM_PROMPT = """You are a planner.

Available tools:
- expense_ratio: savings rate, expense ratio
- expense_concentration: category dominance (requires expense_categories)
- asset_concentration: asset class dominance (requires asset_allocation)
- liquidity: months of coverage (requires current_savings)

Select which tools should run given the financial context below.
Return JSON only, no other text:
{"tools": ["expense_ratio", ...]}
"""


def _context_summary(ctx: FinancialContext) -> str:
    """Build a brief context summary for the planner."""
    parts = [
        f"income: {ctx.income}",
        f"total_expenses: {ctx.total_expenses}",
        f"expense_categories: {len(ctx.expense_categories)}",
        f"asset_allocation: {len(ctx.asset_allocation)}",
        f"current_savings: {ctx.current_savings}",
    ]
    return "\n".join(parts)


def select_tools(
    ctx: FinancialContext,
    capabilities_agent: bool,
    api_key: str | None,
    trace: Dict[str, Any],
) -> List[str]:
    """
    Select tools to run. If planner disabled or fails, return ALL_PLANNER_TOOLS.
    Never crashes; fallback is mandatory.
    """
    trace["planner_used"] = capabilities_agent
    if not capabilities_agent or not api_key or not api_key.strip():
        trace["planner_status"] = "skipped"
        trace["tools_selected"] = PLANNER_TOOL_NAMES.copy()
        return PLANNER_TOOL_NAMES.copy()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        summary = _context_summary(ctx)
        prompt = f"{PLANNER_SYSTEM_PROMPT}\n\nContext:\n{summary}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            trace["planner_status"] = "fallback"
            trace["tools_selected"] = PLANNER_TOOL_NAMES.copy()
            return PLANNER_TOOL_NAMES.copy()

        # Extract JSON if wrapped in markdown or prose
        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start and (start > 0 or end < len(text)):
            text = text[start:end]

        parsed = ToolSelection.model_validate_json(text)
        selected = [t for t in parsed.tools if t in TOOL_REGISTRY]
        if not selected:
            trace["planner_status"] = "fallback"
            trace["tools_selected"] = PLANNER_TOOL_NAMES.copy()
            return PLANNER_TOOL_NAMES.copy()

        trace["planner_status"] = "valid"
        trace["tools_selected"] = selected
        return selected
    except Exception:
        trace["planner_status"] = "fallback"
        trace["tools_selected"] = PLANNER_TOOL_NAMES.copy()
        return PLANNER_TOOL_NAMES.copy()
