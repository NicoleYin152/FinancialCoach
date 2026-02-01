import { ChevronDown, ChevronUp } from "lucide-react";
import type { FinancialInput } from "./InputPanel";

interface ContextPreviewProps {
  input: FinancialInput;
  expanded: boolean;
  onToggle: () => void;
  onEdit?: () => void;
}

export function ContextPreview({
  input,
  expanded,
  onToggle,
  onEdit,
}: ContextPreviewProps) {
  const income = Number.parseFloat(input.monthly_income) || 0;
  const categorySum =
    input.expense_categories?.reduce(
      (s, c) => s + (Number.parseFloat(c.amount) || 0),
      0
    ) ?? 0;
  const expenses =
    categorySum > 0 ? categorySum : Number.parseFloat(input.monthly_expenses) || 0;
  const savings = input.current_savings
    ? Number.parseFloat(input.current_savings)
    : null;
  const hasData = income > 0 || expenses > 0;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-md dark:border-slate-700 dark:bg-slate-800">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Financial Context
        </span>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        )}
      </button>
      {expanded && (
        <div className="border-t border-slate-200 px-4 py-3 dark:border-slate-700">
          {!hasData ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No data yet. Use the edit panel to add income and expenses.
            </p>
          ) : (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-600 dark:text-slate-400">Income</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">
                  ${income.toLocaleString()}/mo
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600 dark:text-slate-400">Expenses</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">
                  ${expenses.toLocaleString()}/mo
                </dd>
              </div>
              {income > 0 && (
                <div className="flex justify-between">
                  <dt className="text-slate-600 dark:text-slate-400">Savings rate</dt>
                  <dd className="font-medium text-slate-900 dark:text-slate-100">
                    {(((income - expenses) / income) * 100).toFixed(1)}%
                  </dd>
                </div>
              )}
              {savings != null && !Number.isNaN(savings) && (
                <div className="flex justify-between">
                  <dt className="text-slate-600 dark:text-slate-400">Current savings</dt>
                  <dd className="font-medium text-slate-900 dark:text-slate-100">
                    ${savings.toLocaleString()}
                  </dd>
                </div>
              )}
              {input.expense_categories && input.expense_categories.length > 0 && (
                <div>
                  <dt className="mb-1 text-slate-600 dark:text-slate-400">Categories</dt>
                  <dd className="flex flex-wrap gap-2">
                    {input.expense_categories.map((c) => (
                      <span
                        key={c.category}
                        className="rounded bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-700"
                      >
                        {c.category}: ${Number(c.amount).toLocaleString()}
                      </span>
                    ))}
                  </dd>
                </div>
              )}
              {input.asset_allocation && input.asset_allocation.length > 0 && (
                <div>
                  <dt className="mb-1 text-slate-600 dark:text-slate-400">Assets</dt>
                  <dd className="flex flex-wrap gap-2">
                    {input.asset_allocation.map((a) => (
                      <span
                        key={a.asset_class}
                        className="rounded bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-700"
                      >
                        {a.asset_class}: {Number(a.allocation_pct).toFixed(0)}%
                      </span>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          )}
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              className="mt-3 text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              Edit context
            </button>
          )}
        </div>
      )}
    </div>
  );
}
