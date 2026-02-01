import { motion } from "framer-motion";
import { AlertTriangle, Info } from "lucide-react";
import { DIMENSION_LABELS, RISK_COLORS } from "../utils/mappings";
import { Tooltip } from "./Tooltip";
import type { AnalysisItem } from "../services/agentApi";

interface RiskCardProps {
  finding: AnalysisItem;
  highlighted?: boolean;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function RiskCard({
  finding,
  highlighted = false,
  onMouseEnter,
  onMouseLeave,
}: RiskCardProps) {
  const colors = RISK_COLORS[finding.risk_level] ?? RISK_COLORS.invalid;
  const label = DIMENSION_LABELS[finding.dimension] ?? finding.dimension;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className={`rounded-xl border p-4 transition-shadow ${
        highlighted
          ? "ring-2 ring-indigo-500 shadow-lg dark:ring-indigo-400"
          : "border-slate-200 shadow-md dark:border-slate-700"
      } ${colors.bg} ${colors.border}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className={`h-5 w-5 shrink-0 ${colors.text}`} />
            <h3 className={`font-semibold ${colors.text}`}>{label}</h3>
            <Tooltip content={finding.reason} side="top">
              <Info className="h-4 w-4 shrink-0 cursor-help text-slate-400" />
            </Tooltip>
          </div>
          <p className={`mt-1 text-sm ${colors.text} opacity-90`}>
            {finding.reason}
          </p>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${colors.text}`}
        >
          {finding.risk_level}
        </span>
      </div>
    </motion.div>
  );
}
