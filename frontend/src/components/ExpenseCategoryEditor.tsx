import { motion } from "framer-motion";
import { Plus, Trash2 } from "lucide-react";

const PREDEFINED_CATEGORIES = [
  "Housing",
  "Food",
  "Transport",
  "Utilities",
  "Healthcare",
  "Entertainment",
  "Other",
];

export interface ExpenseCategoryRow {
  category: string;
  amount: string;
}

interface ExpenseCategoryEditorProps {
  categories: ExpenseCategoryRow[];
  onChange: (categories: ExpenseCategoryRow[]) => void;
  disabled?: boolean;
}

export function ExpenseCategoryEditor({
  categories,
  onChange,
  disabled = false,
}: ExpenseCategoryEditorProps) {
  const update = (index: number, field: keyof ExpenseCategoryRow, value: string) => {
    const next = [...categories];
    next[index] = { ...next[index], [field]: value };
    onChange(next);
  };

  const addRow = () => {
    onChange([...categories, { category: "", amount: "" }]);
  };

  const removeRow = (index: number) => {
    const next = categories.filter((_, i) => i !== index);
    onChange(next);
  };

  const total = categories.reduce((sum, row) => {
    const amt = Number.parseFloat(row.amount) || 0;
    return sum + amt;
  }, 0);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-600">
        <table className="w-full min-w-[320px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-600 dark:bg-slate-800/50">
              <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-300">
                Category
              </th>
              <th className="px-3 py-2 text-right font-medium text-slate-700 dark:text-slate-300">
                Amount
              </th>
              {!disabled && (
                <th className="w-10 px-2 py-2" aria-label="Actions" />
              )}
            </tr>
          </thead>
          <tbody>
            {categories.map((row, i) => (
              <tr
                key={i}
                className="border-b border-slate-100 last:border-0 dark:border-slate-700"
              >
                <td className="px-3 py-2">
                  <input
                    type="text"
                    list={`expense-categories-${i}`}
                    placeholder="e.g. Housing, Food"
                    value={row.category}
                    onChange={(e) => update(i, "category", e.target.value)}
                    disabled={disabled}
                    className="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-slate-900 placeholder-slate-400 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                  <datalist id={`expense-categories-${i}`}>
                    {PREDEFINED_CATEGORIES.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </td>
                <td className="px-3 py-2 text-right">
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0"
                    value={row.amount}
                    onChange={(e) => update(i, "amount", e.target.value)}
                    disabled={disabled}
                    className="w-24 rounded border border-slate-300 bg-white px-2 py-1.5 text-right text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  />
                </td>
                {!disabled && (
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      onClick={() => removeRow(i)}
                      className="rounded p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-900/20 dark:hover:text-rose-400"
                      aria-label="Remove row"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!disabled && (
        <motion.button
          type="button"
          whileTap={{ scale: 0.97 }}
          onClick={addRow}
          className="flex items-center gap-2 rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 hover:border-indigo-500 hover:text-indigo-600 dark:border-slate-600 dark:text-slate-400 dark:hover:border-indigo-500 dark:hover:text-indigo-400"
        >
          <Plus className="h-4 w-4" />
          Add row
        </motion.button>
      )}
      {total > 0 && (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Total: ${total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </p>
      )}
    </div>
  );
}
