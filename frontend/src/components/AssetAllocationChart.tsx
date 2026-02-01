import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { AssetAllocation } from "../services/agentApi";

const CHART_COLORS = ["#6366f1", "#34d399", "#fbbf24", "#fb7185", "#a78bfa"];

interface AssetAllocationChartProps {
  allocation: AssetAllocation[];
  highlighted?: boolean;
}

export function AssetAllocationChart({
  allocation,
  highlighted = false,
}: AssetAllocationChartProps) {
  if (!allocation || allocation.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-600 dark:bg-slate-800/50"
      >
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Add asset allocation data to see chart
        </p>
      </motion.div>
    );
  }

  const data = allocation.map((a, i) => ({
    name: a.asset_class,
    value: a.allocation_pct,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-md transition-all dark:border-slate-700 dark:bg-slate-800 ${
        highlighted ? "ring-2 ring-indigo-500 dark:ring-indigo-400" : ""
      }`}
    >
      <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Asset Allocation
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
                value != null ? [`${Number(value).toFixed(1)}%`, undefined] : null
              }
            />
            <Legend
              content={({ payload }) => (
                <ul className="flex flex-wrap justify-center gap-4 pt-2">
                  {payload?.map((entry, i) => (
                    <li
                      key={i}
                      className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400"
                    >
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      {entry.value} ({(entry.payload?.value ?? 0).toFixed(1)}%)
                    </li>
                  ))}
                </ul>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
