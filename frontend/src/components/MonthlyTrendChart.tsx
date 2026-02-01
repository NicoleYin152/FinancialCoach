import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import type { MonthlyDataPoint } from "../utils/sampleDataGenerator";

interface MonthlyTrendChartProps {
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlyData?: MonthlyDataPoint[] | null;
  highlighted?: boolean;
}

export function MonthlyTrendChart({
  monthlyIncome,
  monthlyExpenses,
  monthlyData,
  highlighted = false,
}: MonthlyTrendChartProps) {
  const singleData = [
    { name: "Income", value: monthlyIncome, color: "#34d399" },
    { name: "Expenses", value: monthlyExpenses, color: "#fb7185" },
  ];
  const hasTrendData = monthlyData && monthlyData.length > 0;
  const trendData = hasTrendData
    ? monthlyData!.map((d) => ({
        month: d.month,
        income: d.income,
        expenses: d.expenses,
      }))
    : null;

  if (!hasTrendData && monthlyIncome <= 0 && monthlyExpenses <= 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-600 dark:bg-slate-800/50"
      >
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Add income/expense data to see trend
        </p>
      </motion.div>
    );
  }

  if (hasTrendData && trendData) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`rounded-xl border border-slate-200 bg-white p-6 shadow-md transition-all dark:border-slate-700 dark:bg-slate-800 ${
          highlighted ? "ring-2 ring-indigo-500 dark:ring-indigo-400" : ""
        }`}
      >
        <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-300">
          Income vs Expenses (Trend)
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.5} />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} width={50} />
              <Tooltip
                formatter={(value) =>
                value != null ? [`$${Number(value).toLocaleString()}`, undefined] : null
              }
                labelFormatter={(label) => `Month: ${label}`}
              />
              <Area
                type="monotone"
                dataKey="income"
                stroke="#34d399"
                fill="#34d399"
                fillOpacity={0.3}
                name="Income"
              />
              <Area
                type="monotone"
                dataKey="expenses"
                stroke="#fb7185"
                fill="#fb7185"
                fillOpacity={0.3}
                name="Expenses"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
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
        Income vs Expenses
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={singleData} layout="vertical" margin={{ left: 0, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.5} />
            <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <YAxis type="category" dataKey="name" width={60} />
            <Tooltip
              formatter={(value) =>
                value != null ? [`$${Number(value).toLocaleString()}`, undefined] : null
              }
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {singleData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
