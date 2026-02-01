import { useState } from "react";

export interface FinancialInputValue {
  monthly_income?: string;
  monthly_expenses?: string;
  current_savings?: string;
}

interface FinancialInputEditorProps {
  value: FinancialInputValue;
  onSubmit: (data: FinancialInputValue) => void;
  disabled?: boolean;
}

export function FinancialInputEditor({
  value,
  onSubmit,
  disabled = false,
}: FinancialInputEditorProps) {
  const [income, setIncome] = useState(value.monthly_income ?? "");
  const [expenses, setExpenses] = useState(value.monthly_expenses ?? "");
  const [savings, setSavings] = useState(value.current_savings ?? "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      monthly_income: income,
      monthly_expenses: expenses,
      current_savings: savings || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-800/50">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Monthly Income
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="e.g. 8000"
          value={income}
          onChange={(e) => setIncome(e.target.value)}
          disabled={disabled}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Monthly Expenses
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="e.g. 5500"
          value={expenses}
          onChange={(e) => setExpenses(e.target.value)}
          disabled={disabled}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
          Current Savings (optional)
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="e.g. 15000"
          value={savings}
          onChange={(e) => setSavings(e.target.value)}
          disabled={disabled}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !income || !expenses}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Submit
      </button>
    </form>
  );
}
