"""Tool registry for composable analysis. Enables selective execution and future agent-decided tool calling."""

from typing import Dict, List, TYPE_CHECKING

from tools.context import FinancialContext
from tools.schemas import ToolResult
from tools.input_validation_tool import InputValidationTool
from tools.expense_ratio_tool import ExpenseRatioTool
from tools.expense_concentration_tool import ExpenseConcentrationTool
from tools.asset_concentration_tool import AssetConcentrationTool
from tools.liquidity_tool import LiquidityTool

if TYPE_CHECKING:
    from tools.tool_protocol import AnalysisTool


TOOL_REGISTRY: Dict[str, "AnalysisTool"] = {
    "input_validation": InputValidationTool(),
    "expense_ratio": ExpenseRatioTool(),
    "expense_concentration": ExpenseConcentrationTool(),
    "asset_concentration": AssetConcentrationTool(),
    "liquidity": LiquidityTool(),
}

# Planner-selectable tools (excludes input_validation which always runs first)
PLANNER_TOOL_NAMES = ["expense_ratio", "expense_concentration", "asset_concentration", "liquidity"]

ALL_PLANNER_TOOLS = [TOOL_REGISTRY[k] for k in PLANNER_TOOL_NAMES]


def run_tools(
    ctx: FinancialContext,
    selected_tool_names: List[str] | None = None,
) -> tuple[List[ToolResult], List[str], List[str]]:
    """
    Run applicable tools on the context.
    If selected_tool_names is None, run all planner-selectable tools.
    input_validation always runs first.
    Returns (results, tools_executed, metrics_computed).
    """
    results: List[ToolResult] = []
    tools_executed: List[str] = []
    metrics_computed: List[str] = list(ctx.derived_metrics.keys())

    # Input validation always runs first; if invalid, skip other tools
    input_tool = TOOL_REGISTRY["input_validation"]
    if input_tool.applicable(ctx):
        tool_results = input_tool.run(ctx)
        if isinstance(tool_results, list):
            results.extend(tool_results)
        else:
            results.append(tool_results)
        tools_executed.append(input_tool.name)

        invalid_found = any(r.severity == "invalid" for r in results)
        if invalid_found:
            return results, tools_executed, metrics_computed

    # Determine which planner tools to run
    tools_to_run = (
        [TOOL_REGISTRY[k] for k in selected_tool_names if k in TOOL_REGISTRY]
        if selected_tool_names
        else ALL_PLANNER_TOOLS
    )

    for tool in tools_to_run:
        if tool.name == "input_validation":
            continue
        if tool.applicable(ctx):
            tool_results = tool.run(ctx)
            if isinstance(tool_results, list):
                results.extend(tool_results)
            else:
                results.append(tool_results)
            tools_executed.append(tool.name)
            for r in (tool_results if isinstance(tool_results, list) else [tool_results]):
                metrics_computed.extend(r.metrics.keys())

    return results, tools_executed, list(dict.fromkeys(metrics_computed))
