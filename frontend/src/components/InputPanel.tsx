import { motion } from "framer-motion";
import { Calculator, Loader2 } from "lucide-react";

export interface FinancialInput {
  monthly_income: string;
  monthly_expenses: string;
  current_savings?: string;
  risk_tolerance?: string;
}

interface InputPanelProps {
  input: FinancialInput;
  onInputChange: (input: FinancialInput) => void;
  onRun: () => void;
  disabled?: boolean;
  loading?: boolean;
  error?: string;
}

export function InputPanel({
  input,
  onInputChange,
  onRun,
  disabled = false,
  loading = false,
  error,
}: InputPanelProps) {
  const update = (field: keyof FinancialInput, value: string) => {
    onInputChange({ ...input, [field]: value });
  };

  const handleRun = () => {
    if (disabled || loading) return;
    const income = Number.parseFloat(input.monthly_income);
    const expenses = Number.parseFloat(input.monthly_expenses);
    if (Number.isNaN(income) || income <= 0) return;
    if (Number.isNaN(expenses) || expenses < 0) return;
    onRun();
  };

  const income = Number.parseFloat(input.monthly_income);
  const expenses = Number.parseFloat(input.monthly_expenses);
  const canRun =
    !Number.isNaN(income) &&
    income > 0 &&
    !Number.isNaN(expenses) &&
    expenses >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-md dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="mb-4 flex items-center gap-2">
        <Calculator className="h-5 w-5 text-slate-500" />
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Financial Input
        </h2>
      </div>
      <div className="space-y-4">
        <div>
          <label
            htmlFor="monthly_income"
            className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Monthly Income
          </label>
          <input
            id="monthly_income"
            type="number"
            min="0"
            step="0.01"
            placeholder="e.g. 8000"
            value={input.monthly_income}
            onChange={(e) => update("monthly_income", e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
        </div>
        <div>
          <label
            htmlFor="monthly_expenses"
            className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Monthly Expenses
          </label>
          <input
            id="monthly_expenses"
            type="number"
            min="0"
            step="0.01"
            placeholder="e.g. 5500"
            value={input.monthly_expenses}
            onChange={(e) => update("monthly_expenses", e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
        </div>
        <div>
          <label
            htmlFor="current_savings"
            className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Current Savings (optional)
          </label>
          <input
            id="current_savings"
            type="number"
            min="0"
            step="0.01"
            placeholder="e.g. 15000"
            value={input.current_savings ?? ""}
            onChange={(e) => update("current_savings", e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
        </div>
        <div>
          <label
            htmlFor="risk_tolerance"
            className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Risk Tolerance (optional)
          </label>
          <select
            id="risk_tolerance"
            value={input.risk_tolerance ?? ""}
            onChange={(e) => update("risk_tolerance", e.target.value || "")}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            <option value="">Select...</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>
      {error && (
        <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">{error}</p>
      )}
      <motion.button
        whileHover={canRun && !loading ? { scale: 1.01 } : {}}
        whileTap={canRun && !loading ? { scale: 0.97 } : {}}
        onClick={handleRun}
        disabled={!canRun || loading}
        className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-3 font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Analyzing your finances...
          </>
        ) : (
          "Analyze My Finances"
        )}
      </motion.button>
    </motion.div>
  );
}
