import { motion } from "framer-motion";
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  PolarAngleAxis,
} from "recharts";

interface SavingsGaugeProps {
  savingsRate: number;
  highlighted?: boolean;
}

const EMERALD_400 = "#34d399";
const AMBER_400 = "#fbbf24";
const ROSE_400 = "#fb7185";

function getColor(pct: number): string {
  if (pct >= 20) return EMERALD_400;
  if (pct >= 10) return AMBER_400;
  return ROSE_400;
}

export function SavingsGauge({
  savingsRate,
  highlighted = false,
}: SavingsGaugeProps) {
  const pct = Math.min(Math.max(savingsRate * 100, 0), 100);
  const data = [{ name: "savings", value: pct, fill: getColor(pct) }];

  return (
    <motion.div
      key={pct}
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-md transition-all dark:border-slate-700 dark:bg-slate-800 ${
        highlighted ? "ring-2 ring-indigo-500 dark:ring-indigo-400" : ""
      }`}
    >
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="60%"
            outerRadius="100%"
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              background
              dataKey="value"
              cornerRadius={8}
              label={{
                position: "center",
                content: () => (
                  <text x="50%" y="48%" textAnchor="middle" dominantBaseline="middle">
                    <tspan
                      x="50%"
                      dy="0"
                      className="fill-slate-900 text-2xl font-bold dark:fill-slate-100"
                    >
                      {pct.toFixed(1)}%
                    </tspan>
                    <tspan
                      x="50%"
                      dy="24"
                      className="fill-slate-600 text-xs dark:fill-slate-400"
                    >
                      Savings Rate
                    </tspan>
                  </text>
                ),
              }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
