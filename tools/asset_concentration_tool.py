"""Asset concentration tool: asset class dominance, diversification risk (structural only)."""

from tools.context import FinancialContext
from tools.schemas import ToolResult


class AssetConcentrationTool:
    """Analysis tool for asset allocation concentration. Structural guidance only—not investment advice."""

    name = "asset_concentration"
    dimension = "AssetConcentration"

    def applicable(self, ctx: FinancialContext) -> bool:
        return bool(ctx.asset_allocation)

    def run(self, ctx: FinancialContext) -> list[ToolResult]:
        results: list[ToolResult] = []

        for ac_name, pct in ctx.asset_allocation.items():
            if pct <= 0:
                continue
            if pct > 80:
                results.append(
                    ToolResult(
                        tool_name=self.name,
                        dimension=self.dimension,
                        severity="high",
                        reason=f"Single asset class ({ac_name}) exceeds 80%",
                        metrics={
                            "largest_asset_pct": pct,
                            "dominant_asset_class": ac_name,
                        },
                    )
                )
                break
            elif pct > 60:
                results.append(
                    ToolResult(
                        tool_name=self.name,
                        dimension=self.dimension,
                        severity="medium",
                        reason=f"Single asset class ({ac_name}) exceeds 60%",
                        metrics={
                            "largest_asset_pct": pct,
                            "dominant_asset_class": ac_name,
                        },
                    )
                )
                break

        return results
