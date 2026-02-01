"""Tool registry for composable analysis. Enables selective execution and future agent-decided tool calling."""

from typing import Dict, List

from tools.context import FinancialContext
from tools.tool_protocol import AnalysisTool, ToolResult
from tools.input_validation_tool import InputValidationTool
from tools.expense_ratio_tool import ExpenseRatioTool
from tools.expense_concentration_tool import ExpenseConcentrationTool
from tools.asset_concentration_tool import AssetConcentrationTool
from tools.liquidity_tool import LiquidityTool


TOOL_REGISTRY: Dict[str, AnalysisTool] = {
    "input_validation": InputValidationTool(),
    "expense_ratio": ExpenseRatioTool(),
    "expense_concentration": ExpenseConcentrationTool(),
    "asset_concentration": AssetConcentrationTool(),
    "liquidity": LiquidityTool(),
}


def run_tools(ctx: FinancialContext) -> tuple[List[ToolResult], List[str], List[str]]:
    """
    Run all applicable tools on the context.
    Returns (results, tools_executed, metrics_computed).
    """
    results: List[ToolResult] = []
    tools_executed: List[str] = []
    metrics_computed: List[str] = list(ctx.derived_metrics.keys())

    # Input validation runs first; if invalid, skip other tools
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

    for key, tool in TOOL_REGISTRY.items():
        if key == "input_validation":
            continue
        if tool.applicable(ctx):
            tool_results = tool.run(ctx)
            if isinstance(tool_results, list):
                results.extend(tool_results)
            else:
                results.append(tool_results)
            tools_executed.append(tool.name)
            for r in (tool_results if isinstance(tool_results, list) else [tool_results]):
                metrics_computed.extend(r.supporting_metrics.keys())

    return results, tools_executed, list(dict.fromkeys(metrics_computed))
