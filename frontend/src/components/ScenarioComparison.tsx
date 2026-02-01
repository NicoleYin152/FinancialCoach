import { motion } from "framer-motion";
import { GitCompare, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { AgentResponse } from "../services/agentApi";

interface ScenarioComparisonProps {
  baseline: AgentResponse;
  scenario: AgentResponse;
  scenarioLabel?: string;
}

function severityRank(s: string): number {
  if (s === "invalid") return 4;
  if (s === "high") return 3;
  if (s === "medium") return 2;
  return 1;
}

function severityDiff(
  base: string,
  scen: string
): "improved" | "worsened" | "unchanged" {
  const rBase = severityRank(base);
  const rScen = severityRank(scen);
  if (rScen < rBase) return "improved";
  if (rScen > rBase) return "worsened";
  return "unchanged";
}

export function ScenarioComparison({
  baseline,
  scenario,
  scenarioLabel = "Scenario",
}: ScenarioComparisonProps) {
  const baseByDim = new Map(
    baseline.analysis?.map((a) => [a.dimension, a]) ?? []
  );
  const scenByDim = new Map(
    scenario.analysis?.map((a) => [a.dimension, a]) ?? []
  );

  const allDims = new Set([...baseByDim.keys(), ...scenByDim.keys()]);
  const diffs: Array<{
    dimension: string;
    baseSeverity: string;
    scenSeverity: string;
    diff: "improved" | "worsened" | "unchanged";
    baseReason: string;
    scenReason: string;
  }> = [];

  for (const dim of allDims) {
    const b = baseByDim.get(dim);
    const s = scenByDim.get(dim);
    const bSev = b?.risk_level ?? "ok";
    const sSev = s?.risk_level ?? "ok";
    diffs.push({
      dimension: dim,
      baseSeverity: bSev,
      scenSeverity: sSev,
      diff: severityDiff(bSev, sSev),
      baseReason: b?.reason ?? "",
      scenReason: s?.reason ?? "",
    });
  }

  const improved = diffs.filter((d) => d.diff === "improved");
  const worsened = diffs.filter((d) => d.diff === "worsened");

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-6 dark:border-indigo-800 dark:bg-indigo-950/30"
    >
      <div className="mb-4 flex items-center gap-2">
        <GitCompare className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Scenario Comparison: Baseline vs {scenarioLabel}
        </h3>
      </div>

      <div className="space-y-3">
        {improved.length > 0 && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 dark:border-emerald-800 dark:bg-emerald-950/30">
            <p className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-800 dark:text-emerald-300">
              <TrendingUp className="h-4 w-4" />
              Improved
            </p>
            <ul className="space-y-1 text-sm text-emerald-700 dark:text-emerald-400">
              {improved.map((d) => (
                <li key={d.dimension}>
                  <strong>{d.dimension}</strong>: {d.baseSeverity} → {d.scenSeverity}
                  {d.scenReason && (
                    <span className="ml-1 text-emerald-600 dark:text-emerald-500">
                      — {d.scenReason}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {worsened.length > 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="mb-2 flex items-center gap-2 text-sm font-medium text-amber-800 dark:text-amber-300">
              <TrendingDown className="h-4 w-4" />
              Worsened
            </p>
            <ul className="space-y-1 text-sm text-amber-700 dark:text-amber-400">
              {worsened.map((d) => (
                <li key={d.dimension}>
                  <strong>{d.dimension}</strong>: {d.baseSeverity} → {d.scenSeverity}
                  {d.scenReason && (
                    <span className="ml-1 text-amber-600 dark:text-amber-500">
                      — {d.scenReason}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {improved.length === 0 && worsened.length === 0 && (
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
            <Minus className="h-4 w-4 text-slate-500" />
            <p className="text-sm text-slate-600 dark:text-slate-400">
              No severity changes between baseline and scenario
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
