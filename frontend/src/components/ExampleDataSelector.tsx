import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import type { FinancialInput } from "./InputPanel";

const PRESETS: { id: string; label: string; data: FinancialInput }[] = [
  {
    id: "struggling",
    label: "Struggling",
    data: {
      monthly_income: "4000",
      monthly_expenses: "3800",
      current_savings: "500",
      risk_tolerance: "low",
    },
  },
  {
    id: "moderate",
    label: "Moderate",
    data: {
      monthly_income: "8000",
      monthly_expenses: "5500",
      current_savings: "15000",
      risk_tolerance: "medium",
    },
  },
  {
    id: "comfortable",
    label: "Comfortable",
    data: {
      monthly_income: "15000",
      monthly_expenses: "9000",
      current_savings: "50000",
      risk_tolerance: "high",
    },
  },
];

interface ExampleDataSelectorProps {
  onSelect: (input: FinancialInput) => void;
  selectedId?: string;
}

export function ExampleDataSelector({
  onSelect,
  selectedId,
}: ExampleDataSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-md dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-slate-500" />
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Example Presets
        </h2>
      </div>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
        Use preset data to explore the analysis.
      </p>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <motion.button
            key={preset.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelect(preset.data)}
            className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              selectedId === preset.id
                ? "bg-indigo-600 text-white dark:bg-indigo-500"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            }`}
          >
            {preset.label}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
