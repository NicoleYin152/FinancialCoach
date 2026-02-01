/** Dimension-to-chart mapping for hover highlighting */
export const DIMENSION_TO_CHART: Record<string, string> = {
  Savings: "SavingsGauge",
  ExpenseRatio: "ExpenseChart",
  Input: "MonthlyTrendChart",
};

/** Risk level colors for UI (Tailwind classes) */
export const RISK_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  high: {
    bg: "bg-rose-50 dark:bg-rose-950/30",
    text: "text-rose-700 dark:text-rose-400",
    border: "border-rose-200 dark:border-rose-800",
  },
  medium: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    text: "text-amber-700 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
  },
  invalid: {
    bg: "bg-slate-50 dark:bg-slate-800/50",
    text: "text-slate-600 dark:text-slate-400",
    border: "border-slate-200 dark:border-slate-700",
  },
};

/** Human-readable labels for dimensions */
export const DIMENSION_LABELS: Record<string, string> = {
  Savings: "Savings Rate",
  ExpenseRatio: "Expense Ratio",
  Input: "Input Validation",
};
