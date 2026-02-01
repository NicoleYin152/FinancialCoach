/** Dimension-to-chart mapping for hover highlighting */
export const DIMENSION_TO_CHART: Record<string, string> = {
  Savings: "SavingsGauge",
  ExpenseRatio: "ExpenseChart",
  ExpenseConcentration: "ExpenseChart",
  AssetConcentration: "AssetAllocationChart",
  Liquidity: "SavingsGauge",
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
  ExpenseConcentration: "Expense Concentration",
  AssetConcentration: "Asset Concentration",
  Liquidity: "Liquidity",
  Input: "Input Validation",
};

/** Alias map for expense category normalization (lowercase key → display/API value) */
export const CATEGORY_ALIASES: Record<string, string> = {
  transport: "Transport",
  transportation: "Transport",
  car: "Transport",
  auto: "Transport",
  dining: "Dining",
  food: "Dining",
  groceries: "Food",
  rent: "Housing",
  housing: "Housing",
  mortgage: "Housing",
  utilities: "Utilities",
  healthcare: "Healthcare",
  health: "Healthcare",
  entertainment: "Entertainment",
  other: "Other",
};

function capitalize(s: string): string {
  const t = s.trim();
  if (!t) return s;
  return t.charAt(0).toUpperCase() + t.slice(1).toLowerCase();
}

/** Normalize expense category for display and API (trim, lowercase, alias map, then capitalize). */
export function normalizeCategory(raw: string): string {
  const key = raw.trim().toLowerCase();
  return CATEGORY_ALIASES[key] ?? capitalize(key.trim());
}
