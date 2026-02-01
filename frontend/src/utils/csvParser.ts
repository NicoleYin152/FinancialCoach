export interface ParsedFinancials {
  monthly_income?: number;
  monthly_expenses: number;
  expense_categories?: { category: string; amount: number }[];
}

export interface ParseResult {
  success: true;
  data: ParsedFinancials;
}

export interface ParseError {
  success: false;
  error: string;
}

export type CsvParseResult = ParseResult | ParseError;

/**
 * Supported CSV formats:
 * - date, income, expenses (header row)
 * - date, amount, type (where type is "income" or "expense")
 * - month, income, expenses
 */
const INCOME_ALIASES = ["income", "monthly_income", "revenue"];
const EXPENSE_ALIASES = ["expenses", "monthly_expenses", "expense"];

function parseFloatSafe(val: string): number {
  const cleaned = val.replace(/[$,]/g, "").trim();
  const n = Number.parseFloat(cleaned);
  return Number.isNaN(n) ? 0 : n;
}

function findColumnIndex(headers: string[], aliases: string[]): number {
  const normalized = headers.map((h) => h.toLowerCase().replace(/\s+/g, "_"));
  for (const alias of aliases) {
    const idx = normalized.findIndex((h) => h.includes(alias) || alias.includes(h));
    if (idx >= 0) return idx;
  }
  return -1;
}

/**
 * Parse CSV string and derive monthly averages for income and expenses.
 * Returns { monthly_income, monthly_expenses } or parse error.
 */
export function parseCsvToFinancials(csvText: string): CsvParseResult {
  const lines = csvText.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) {
    return { success: false, error: "CSV must have header and at least one data row" };
  }

  const headerLine = lines[0];
  const headers = headerLine.split(",").map((h) => h.trim());
  const incomeIdx = findColumnIndex(headers, INCOME_ALIASES);
  const expenseIdx = findColumnIndex(headers, EXPENSE_ALIASES);

  if (incomeIdx >= 0 && expenseIdx >= 0) {
    // Format A: month, income, expenses (monthly aggregates)
    let totalIncome = 0;
    let totalExpenses = 0;
    let rowCount = 0;
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim());
      const inc = parseFloatSafe(cols[incomeIdx] ?? "0");
      const exp = parseFloatSafe(cols[expenseIdx] ?? "0");
      if (Number.isNaN(inc) || Number.isNaN(exp)) {
        return { success: false, error: `Row ${i + 1}: income and expenses must be valid numbers` };
      }
      if (exp < 0) {
        return { success: false, error: `Row ${i + 1}: expenses cannot be negative` };
      }
      if (inc > 0 || exp > 0) {
        totalIncome += inc;
        totalExpenses += exp;
        rowCount++;
      }
    }
    if (rowCount === 0) {
      return { success: false, error: "No valid income or expense values found" };
    }
    return {
      success: true,
      data: {
        monthly_income: totalIncome / rowCount,
        monthly_expenses: totalExpenses / rowCount,
      },
    };
  }

  // Format B: month, category, amount (categorized expenses - aggregate by category)
  const categoryIdx = headers.findIndex((h) => /category/i.test(h) && !/type/i.test(h));
  const amountIdxB = headers.findIndex((h) => /amount|value/i.test(h));
  const monthIdx = headers.findIndex((h) => /month|date|period/i.test(h));
  if (categoryIdx >= 0 && amountIdxB >= 0) {
    const categoryTotals: Record<string, number> = {};
    let totalIncome = 0;
    const monthsSeen = new Set<string>();
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim());
      const amtStr = cols[amountIdxB] ?? "";
      const amt = parseFloatSafe(amtStr);
      if (amtStr && Number.isNaN(amt)) {
        return { success: false, error: `Row ${i + 1}: amount "${amtStr}" must be a valid number` };
      }
      if (amt < 0) {
        return { success: false, error: `Row ${i + 1}: amount cannot be negative` };
      }
      const cat = (cols[categoryIdx] ?? "").trim();
      if (!cat) {
        return { success: false, error: `Row ${i + 1}: category cannot be empty` };
      }
      if (monthIdx >= 0) {
        const monthStr = (cols[monthIdx] ?? "").slice(0, 7);
        if (monthStr) monthsSeen.add(monthStr);
      }
      categoryTotals[cat] = (categoryTotals[cat] ?? 0) + amt;
    }
    const monthCount = Math.max(monthsSeen.size || 1, 1);
    const expenseCategories = Object.entries(categoryTotals)
      .map(([category, amount]) => ({ category, amount: amount / monthCount }))
      .filter((c) => c.amount > 0)
      .sort((a, b) => b.amount - a.amount);
    const totalExpenses = expenseCategories.reduce((s, c) => s + c.amount, 0);
    if (expenseCategories.length === 0) {
      return { success: false, error: "No valid expense data found" };
    }
    const data: ParsedFinancials = {
      monthly_expenses: totalExpenses,
      expense_categories: expenseCategories,
    };
    if (totalIncome > 0) {
      data.monthly_income = totalIncome / monthCount;
    }
    return { success: true, data };
  }

  // Format C: date, amount, type (each row is a transaction)
  const amountIdx = headers.findIndex(
    (h) => /amount|value|sum/i.test(h) && !/income|expense/i.test(h)
  );
  const typeIdx = headers.findIndex((h) => /type/i.test(h) && !/category/i.test(h));
  const dateIdx = headers.findIndex((h) => /date|month|period/i.test(h));
  if (amountIdx >= 0 && typeIdx >= 0) {
    let totalIncome = 0;
    let totalExpenses = 0;
    const monthsSeen = new Set<string>();
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim());
      const amt = parseFloatSafe(cols[amountIdx] ?? "0");
      const typ = (cols[typeIdx] ?? "").toLowerCase();
      if (dateIdx >= 0) {
        const dateStr = (cols[dateIdx] ?? "").slice(0, 7);
        if (dateStr) monthsSeen.add(dateStr);
      }
      if (typ.includes("income") || typ === "in") {
        totalIncome += amt;
      } else if (typ.includes("expense") || typ === "out" || typ === "exp") {
        totalExpenses += amt;
      }
    }
    const monthCount = Math.max(monthsSeen.size || 1, 1);
    return {
      success: true,
      data: {
        monthly_income: totalIncome / monthCount,
        monthly_expenses: totalExpenses / monthCount,
      },
    };
  }

  // Fallback: assume first numeric column is income, second is expenses
  const numericCols: number[] = [];
  for (let c = 0; c < headers.length; c++) {
    const val = lines[1]?.split(",")[c]?.trim() ?? "";
    if (/^\d+([.,]\d+)?$/.test(val.replace(/[$]/g, ""))) {
      numericCols.push(c);
    }
  }
  if (numericCols.length >= 2) {
    let totalIncome = 0;
    let totalExpenses = 0;
    let count = 0;
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim());
      const inc = parseFloatSafe(cols[numericCols[0]] ?? "0");
      const exp = parseFloatSafe(cols[numericCols[1]] ?? "0");
      if (inc > 0 || exp > 0) {
        totalIncome += inc;
        totalExpenses += exp;
        count++;
      }
    }
    if (count === 0) {
      return { success: false, error: "No valid numeric values found" };
    }
    return {
      success: true,
      data: {
        monthly_income: totalIncome / count,
        monthly_expenses: totalExpenses / count,
      },
    };
  }

  return {
    success: false,
    error: "Could not detect columns. Supported formats: (1) month, income, expenses (2) month, category, amount (3) date, amount, type",
  };
}
