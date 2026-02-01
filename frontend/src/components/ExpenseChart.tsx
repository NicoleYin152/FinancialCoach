import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface ExpenseChartProps {
  monthlyIncome: number;
  monthlyExpenses: number;
  highlighted?: boolean;
}

export function ExpenseChart({
  monthlyIncome,
  monthlyExpenses,
  highlighted = false,
}: ExpenseChartProps) {
  const savings = Math.max(0, monthlyIncome - monthlyExpenses);
  const total = savings + monthlyExpenses || 1;
  const data = [
    { name: "Savings", value: savings, color: "#34d399", pct: (savings / total) * 100 },
    { name: "Expenses", value: monthlyExpenses, color: "#fb7185", pct: (monthlyExpenses / total) * 100 },
  ].filter((d) => d.value > 0);

  if (monthlyIncome <= 0 && monthlyExpenses <= 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-600 dark:bg-slate-800/50"
      >
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Add income/expense data to see chart
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-md transition-all dark:border-slate-700 dark:bg-slate-800 ${
        highlighted ? "ring-2 ring-indigo-500 dark:ring-indigo-400" : ""
      }`}
    >
      <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Income Allocation
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={3}
              dataKey="value"
              nameKey="name"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) =>
                value != null ? [`$${Number(value).toLocaleString()}`, undefined] : null
              }
            />
            <Legend
              content={({ payload }) => (
                <ul className="flex flex-wrap justify-center gap-4 pt-2">
                  {payload?.map((entry, i) => {
                    const item = data[i];
                    const pct = item?.pct ?? 0;
                    return (
                      <li
                        key={i}
                        className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400"
                      >
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: entry.color }}
                        />
                        {entry.value} ({pct.toFixed(1)}%)
                      </li>
                    );
                  })}
                </ul>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
