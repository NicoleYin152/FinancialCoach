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

export interface ExpenseCategorySample {
  category: string;
  amount: number;
}

export interface AssetAllocationSample {
  asset_class: string;
  allocation_pct: number;
}

export interface FullSampleResult extends SamplePortfolioResult {
  expense_categories?: ExpenseCategorySample[];
  asset_allocation?: AssetAllocationSample[];
}

const EXPENSE_CATEGORY_NAMES = ["Housing", "Food", "Transport", "Utilities", "Healthcare", "Entertainment", "Other"];

/**
 * Generate full sample with income, expenses, expense categories, and asset allocation.
 */
export function generateFullSample(): FullSampleResult {
  const { monthlyData, avgIncome, avgExpenses } = generateSamplePortfolioData();
  const totalExpenses = avgExpenses;
  const shares = [0.35, 0.18, 0.12, 0.08, 0.07, 0.10, 0.10];
  const expense_categories: ExpenseCategorySample[] = EXPENSE_CATEGORY_NAMES.slice(0, 7).map((name, i) => ({
    category: name,
    amount: Math.round(totalExpenses * (shares[i] ?? 0.1) * 100) / 100,
  })).filter((c) => c.amount > 0);

  const assetShares = [0.6, 0.3, 0.1];
  const assetClasses = ["Stocks", "Bonds", "Cash"];
  const asset_allocation: AssetAllocationSample[] = assetClasses.map((ac, i) => ({
    asset_class: ac,
    allocation_pct: Math.round((assetShares[i] ?? 0) * 100),
  }));

  return {
    monthlyData,
    avgIncome,
    avgExpenses,
    expense_categories,
    asset_allocation,
  };
}
