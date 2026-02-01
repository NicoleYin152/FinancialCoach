import { motion } from "framer-motion";
import { Plus, Trash2 } from "lucide-react";

const PREDEFINED_ASSET_CLASSES = ["Stocks", "Bonds", "Cash", "Other"];

export interface AssetAllocationRow {
  asset_class: string;
  allocation_pct: string;
}

interface AssetAllocationEditorProps {
  allocation: AssetAllocationRow[];
  onChange: (allocation: AssetAllocationRow[]) => void;
  disabled?: boolean;
}

export function AssetAllocationEditor({
  allocation,
  onChange,
  disabled = false,
}: AssetAllocationEditorProps) {
  const update = (index: number, field: keyof AssetAllocationRow, value: string) => {
    const next = [...allocation];
    next[index] = { ...next[index], [field]: value };
    onChange(next);
  };

  const addRow = () => {
    onChange([...allocation, { asset_class: "", allocation_pct: "" }]);
  };

  const removeRow = (index: number) => {
    const next = allocation.filter((_, i) => i !== index);
    onChange(next);
  };

  const total = allocation.reduce((sum, row) => {
    const pct = Number.parseFloat(row.allocation_pct) || 0;
    return sum + pct;
  }, 0);
  const isValid = Math.abs(total - 100) < 0.1;

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-600">
        <table className="w-full min-w-[280px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-600 dark:bg-slate-800/50">
              <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-300">
                Asset Class
              </th>
              <th className="px-3 py-2 text-right font-medium text-slate-700 dark:text-slate-300">
                %
              </th>
              {!disabled && (
                <th className="w-10 px-2 py-2" aria-label="Actions" />
              )}
            </tr>
          </thead>
          <tbody>
            {allocation.map((row, i) => (
              <tr
                key={i}
                className="border-b border-slate-100 last:border-0 dark:border-slate-700"
              >
                <td className="px-3 py-2">
                  <input
                    type="text"
                    list={`asset-classes-${i}`}
                    placeholder="e.g. Stocks, Bonds"
                    value={row.asset_class}
                    onChange={(e) => update(i, "asset_class", e.target.value)}
                    disabled={disabled}
                    className="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-slate-900 placeholder-slate-400 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                  <datalist id={`asset-classes-${i}`}>
                    {PREDEFINED_ASSET_CLASSES.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </td>
                <td className="px-3 py-2 text-right">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    placeholder="0"
                    value={row.allocation_pct}
                    onChange={(e) => update(i, "allocation_pct", e.target.value)}
                    disabled={disabled}
                    className="w-20 rounded border border-slate-300 bg-white px-2 py-1.5 text-right text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
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
      <p className={`text-sm ${isValid ? "text-slate-600 dark:text-slate-400" : "text-amber-600 dark:text-amber-400"}`}>
        Total: {total.toFixed(1)}% {!isValid && "(must equal 100%)"}
      </p>
    </div>
  );
}
