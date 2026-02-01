import { motion } from "framer-motion";
import { GitCompare } from "lucide-react";

const CATEGORY_OPTIONS = [
  "Transport",
  "Housing",
  "Food",
  "Utilities",
  "Healthcare",
  "Entertainment",
  "Other",
];

export interface ScenarioDelta {
  category: string;
  amount: number;
}

interface ScenarioDeltaInputProps {
  delta: ScenarioDelta | null;
  onChange: (delta: ScenarioDelta | null) => void;
  disabled?: boolean;
}

export function ScenarioDeltaInput({
  delta,
  onChange,
  disabled = false,
}: ScenarioDeltaInputProps) {
  const update = (field: keyof ScenarioDelta, value: string | number) => {
    const next: ScenarioDelta = delta ?? { category: "Transport", amount: 0 };
    if (field === "category") next.category = String(value);
    else next.amount = Number(value);
    onChange(next);
  };

  const clear = () => onChange(null);

  if (!delta) {
    return (
      <motion.button
        type="button"
        whileTap={{ scale: 0.97 }}
        onClick={() => onChange({ category: "Transport", amount: 500 })}
        disabled={disabled}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 px-4 py-3 text-sm font-medium text-slate-600 hover:border-indigo-500 hover:text-indigo-600 dark:border-slate-600 dark:text-slate-400 dark:hover:border-indigo-500 dark:hover:text-indigo-400 disabled:opacity-50"
      >
        <GitCompare className="h-4 w-4" />
        Add what-if scenario (e.g. +$500 Transport)
      </motion.button>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-800/50">
      <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
        Scenario delta
      </p>
      <div className="flex flex-wrap gap-2">
        <select
          value={delta.category}
          onChange={(e) => update("category", e.target.value)}
          disabled={disabled}
          className="rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          {CATEGORY_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={delta.amount}
            onChange={(e) => update("amount", Number(e.target.value) || 0)}
            disabled={disabled}
            className="w-24 rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            placeholder="0"
          />
          <span className="text-sm text-slate-600 dark:text-slate-400">
            (positive = add expense)
          </span>
        </div>
        <button
          type="button"
          onClick={clear}
          disabled={disabled}
          className="rounded px-3 py-2 text-sm text-slate-500 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-300 disabled:opacity-50"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
