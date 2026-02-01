import { useState } from "react";
import { motion } from "framer-motion";
import { Calculator, ChevronDown, ChevronUp, Loader2, PieChart } from "lucide-react";
import { ExpenseCategoryEditor, type ExpenseCategoryRow } from "./ExpenseCategoryEditor";
import { AssetAllocationEditor, type AssetAllocationRow } from "./AssetAllocationEditor";

export interface FinancialInput {
  monthly_income: string;
  monthly_expenses: string;
  expense_categories?: ExpenseCategoryRow[];
  asset_allocation?: AssetAllocationRow[];
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
  const [expenseBreakdownOpen, setExpenseBreakdownOpen] = useState(false);
  const [assetAllocationOpen, setAssetAllocationOpen] = useState(false);

  const update = (field: keyof FinancialInput, value: string) => {
    onInputChange({ ...input, [field]: value });
  };

  const categories = input.expense_categories ?? [];
  const allocation = input.asset_allocation ?? [];

  const categorySum = categories.reduce(
    (s, r) => s + (Number.parseFloat(r.amount) || 0),
    0
  );
  const allocationTotal = allocation.reduce(
    (s, r) => s + (Number.parseFloat(r.allocation_pct) || 0),
    0
  );
  const allocationValid = Math.abs(allocationTotal - 100) < 0.1;

  const expensesFromCategories = categorySum > 0 ? categorySum : null;

  const handleRun = () => {
    if (disabled || loading) return;
    const income = Number.parseFloat(input.monthly_income);
    if (Number.isNaN(income) || income <= 0) return;
    const exp = expensesFromCategories ?? Number.parseFloat(input.monthly_expenses);
    if (Number.isNaN(exp) || exp < 0) return;
    if (allocation.length > 0 && !allocationValid) return;
    onRun();
  };

  const income = Number.parseFloat(input.monthly_income);
  const hasValidExpenses =
    expensesFromCategories !== null ? expensesFromCategories > 0 : !Number.isNaN(Number.parseFloat(input.monthly_expenses)) && Number.parseFloat(input.monthly_expenses) >= 0;
  const canRun =
    !Number.isNaN(income) &&
    income > 0 &&
    hasValidExpenses &&
    (allocation.length === 0 || allocationValid);

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
            {expensesFromCategories !== null && (
              <span className="ml-2 text-slate-500">(from breakdown: ${expensesFromCategories.toFixed(2)})</span>
            )}
          </label>
          <input
            id="monthly_expenses"
            type="number"
            min="0"
            step="0.01"
            placeholder="e.g. 5500"
            value={expensesFromCategories !== null ? String(expensesFromCategories.toFixed(2)) : input.monthly_expenses}
            onChange={(e) => update("monthly_expenses", e.target.value)}
            disabled={expensesFromCategories !== null}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500 dark:disabled:bg-slate-800"
          />
        </div>
        <div>
          <button
            type="button"
            onClick={() => setExpenseBreakdownOpen((o) => !o)}
            className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Expense breakdown (by category)
            {expenseBreakdownOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {expenseBreakdownOpen && (
            <div className="mt-2">
              <ExpenseCategoryEditor
                categories={categories}
                onChange={(c) => onInputChange({ ...input, expense_categories: c })}
                disabled={disabled}
              />
            </div>
          )}
        </div>
        <div>
          <button
            type="button"
            onClick={() => setAssetAllocationOpen((o) => !o)}
            className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <PieChart className="h-4 w-4" />
            Asset allocation (optional)
            {assetAllocationOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {assetAllocationOpen && (
            <div className="mt-2">
              <AssetAllocationEditor
                allocation={allocation}
                onChange={(a) => onInputChange({ ...input, asset_allocation: a })}
                disabled={disabled}
              />
            </div>
          )}
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
