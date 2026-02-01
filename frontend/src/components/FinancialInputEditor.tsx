import { useState } from "react";
import { ExpenseCategoryEditor } from "./ExpenseCategoryEditor";
import type { ExpenseCategoryRow } from "./ExpenseCategoryEditor";

export interface FinancialInputValue {
  monthly_income?: string;
  monthly_expenses?: string;
  expense_categories?: { category: string; amount: number }[] | ExpenseCategoryRow[];
  current_savings?: string;
}

interface FinancialInputEditorProps {
  value: FinancialInputValue;
  onSubmit: (data: FinancialInputValue) => void;
  disabled?: boolean;
}

function toRows(
  cats: FinancialInputValue["expense_categories"]
): ExpenseCategoryRow[] {
  if (!cats?.length) return [{ category: "", amount: "" }];
  return cats.map((c) => ({
    category: typeof c.category === "string" ? c.category : "",
    amount: typeof (c as { amount?: number }).amount === "number"
      ? String((c as { amount: number }).amount)
      : (c as ExpenseCategoryRow).amount ?? "",
  }));
}

function fromRows(rows: ExpenseCategoryRow[]): { category: string; amount: number }[] {
  return rows
    .filter((r) => r.category?.trim() && !Number.isNaN(Number.parseFloat(r.amount)))
    .map((r) => ({
      category: r.category.trim(),
      amount: Number.parseFloat(r.amount) || 0,
    }));
}

export function FinancialInputEditor({
  value,
  onSubmit,
  disabled = false,
}: FinancialInputEditorProps) {
  const [income, setIncome] = useState(value.monthly_income ?? "");
  const [savings, setSavings] = useState(value.current_savings ?? "");
  const [categories, setCategories] = useState<ExpenseCategoryRow[]>(() =>
    toRows(value.expense_categories)
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cats = fromRows(categories);
    const total = cats.reduce((s, c) => s + c.amount, 0);
    onSubmit({
      monthly_income: income,
      monthly_expenses: total > 0 ? String(total) : undefined,
      expense_categories: cats,
      current_savings: savings || undefined,
    });
  };

  const catTotal = categories.reduce(
    (s, c) => s + (Number.parseFloat(c.amount) || 0),
    0
  );
  const hasIncome = income.trim() !== "" && Number.parseFloat(income) > 0;
  const hasCategories = catTotal > 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-800/50"
    >
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
          Expense breakdown by category
        </label>
        <ExpenseCategoryEditor
          categories={categories}
          onChange={setCategories}
          disabled={disabled}
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
        disabled={disabled || !hasIncome || !hasCategories}
        className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Submit
      </button>
    </form>
  );
}
