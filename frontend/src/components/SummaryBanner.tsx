import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface SummaryBannerProps {
  monthlyIncome: number;
  monthlyExpenses: number;
  savingsRate: number;
  hasData?: boolean;
}

export function SummaryBanner({
  monthlyIncome,
  monthlyExpenses,
  savingsRate,
  hasData = true,
}: SummaryBannerProps) {
  const savings = monthlyIncome - monthlyExpenses;
  const status =
    savingsRate >= 0.2 ? "healthy" : savingsRate >= 0.1 ? "moderate" : "at-risk";

  const StatusIcon =
    status === "healthy" ? TrendingUp : status === "moderate" ? Minus : TrendingDown;
  const statusColors =
    status === "healthy"
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
      : status === "moderate"
        ? "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
        : "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300";

  if (!hasData || (monthlyIncome <= 0 && monthlyExpenses <= 0)) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-600 dark:bg-slate-800/50"
      >
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Run analysis to see summary
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-md dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Monthly Summary
          </h3>
          <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
            ${monthlyIncome.toLocaleString()} income · ${monthlyExpenses.toLocaleString()}{" "}
            expenses
          </p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            ${savings.toLocaleString()} savings · {(savingsRate * 100).toFixed(1)}% rate
          </p>
        </div>
        <div
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${statusColors}`}
        >
          <StatusIcon className="h-4 w-4" />
          {status === "healthy" ? "Healthy" : status === "moderate" ? "Moderate" : "At Risk"}
        </div>
      </div>
    </motion.div>
  );
}
