export interface MonthlyDataPoint {
  month: string;
  income: number;
  expenses: number;
}

export interface SamplePortfolioResult {
  monthlyData: MonthlyDataPoint[];
  avgIncome: number;
  avgExpenses: number;
}

function randomInRange(min: number, max: number): number {
  return Math.round(min + Math.random() * (max - min));
}

/**
 * Generate 6-12 months of fake portfolio data.
 * Income: 4000-12000, Expenses: 2500-9000
 */
export function generateSamplePortfolioData(
  months: number = 6 + Math.floor(Math.random() * 7)
): SamplePortfolioResult {
  const monthlyData: MonthlyDataPoint[] = [];
  const now = new Date();
  let totalIncome = 0;
  let totalExpenses = 0;

  for (let i = months - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const month = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const income = randomInRange(4000, 12000);
    const expenses = randomInRange(2500, Math.min(9000, income - 200));
    monthlyData.push({ month, income, expenses });
    totalIncome += income;
    totalExpenses += expenses;
  }

  return {
    monthlyData,
    avgIncome: totalIncome / months,
    avgExpenses: totalExpenses / months,
  };
}
