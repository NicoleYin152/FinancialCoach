import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Loader2 } from "lucide-react";
import { runAgent, getAgentErrorMessage } from "../services/agentApi";
import type { AgentInput, AgentResponse } from "../services/agentApi";
import type { FinancialInput } from "../components/InputPanel";
import { InputPanel } from "../components/InputPanel";
import { CSVUpload } from "../components/CSVUpload";
import { ExampleDataSelector } from "../components/ExampleDataSelector";
import { SummaryBanner } from "../components/SummaryBanner";
import { RiskCard } from "../components/RiskCard";
import { SavingsGauge } from "../components/SavingsGauge";
import { ExpenseChart } from "../components/ExpenseChart";
import { MonthlyTrendChart } from "../components/MonthlyTrendChart";
import { AIReflectionPanel } from "../components/AIReflectionPanel";
import { DIMENSION_TO_CHART } from "../utils/mappings";
import type { MonthlyDataPoint } from "../utils/sampleDataGenerator";

const DEFAULT_INPUT: FinancialInput = {
  monthly_income: "",
  monthly_expenses: "",
  current_savings: "",
  risk_tolerance: "",
};

function toAgentInput(input: FinancialInput): AgentInput {
  const monthly_income = Number.parseFloat(input.monthly_income) || 0;
  const monthly_expenses = Number.parseFloat(input.monthly_expenses) || 0;
  const current_savings = input.current_savings
    ? Number.parseFloat(input.current_savings)
    : undefined;
  const risk_tolerance = input.risk_tolerance || undefined;
  return {
    monthly_income,
    monthly_expenses,
    ...(current_savings != null && !Number.isNaN(current_savings) && {
      current_savings,
    }),
    ...(risk_tolerance && { risk_tolerance }),
  };
}

export function Dashboard() {
  const [input, setInput] = useState<FinancialInput>(DEFAULT_INPUT);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyDataPoint[] | null>(null);
  const [highlightedDimension, setHighlightedDimension] = useState<string | null>(
    null
  );

  const mutation = useMutation({
    mutationFn: runAgent,
    onSuccess: () => {},
  });

  const handleRun = () => {
    const agentInput = toAgentInput(input);
    if (agentInput.monthly_income <= 0 || agentInput.monthly_expenses < 0) return;
    mutation.mutate(agentInput);
  };

  const handlePresetSelect = (preset: FinancialInput) => {
    setInput(preset);
    setMonthlyData(null);
    const presetId =
      preset.monthly_income === "4000" ? "struggling" :
      preset.monthly_income === "8000" ? "moderate" :
      preset.monthly_income === "15000" ? "comfortable" : null;
    setSelectedPresetId(presetId);
  };

  const handleCsvParsed = (partial: Partial<FinancialInput>) => {
    setInput((prev) => ({ ...prev, ...partial }));
    setSelectedPresetId(null);
    setMonthlyData(null);
  };

  const handleSampleDataGenerated = (data: MonthlyDataPoint[]) => {
    setMonthlyData(data);
  };

  const income = Number.parseFloat(input.monthly_income) || 0;
  const expenses = Number.parseFloat(input.monthly_expenses) || 0;
  const savingsRate = income > 0 ? (income - expenses) / income : 0;
  const response = mutation.data as AgentResponse | undefined;
  const hasResponse = !!response;
  const hasData = income > 0 || expenses > 0;

  const isSavingsHighlighted =
    highlightedDimension === "Savings" ||
    DIMENSION_TO_CHART[highlightedDimension ?? ""] === "SavingsGauge";
  const isExpenseHighlighted =
    highlightedDimension === "ExpenseRatio" ||
    DIMENSION_TO_CHART[highlightedDimension ?? ""] === "ExpenseChart";
  const isTrendHighlighted =
    highlightedDimension === "Input" ||
    DIMENSION_TO_CHART[highlightedDimension ?? ""] === "MonthlyTrendChart";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Smart Financial Coach
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            Enter your financial data and run analysis
          </p>
        </motion.header>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-1">
            <InputPanel
              input={input}
              onInputChange={setInput}
              onRun={handleRun}
              disabled={mutation.isPending}
              loading={mutation.isPending}
              error={
                mutation.isError
                  ? getAgentErrorMessage(mutation.error)
                  : undefined
              }
            />
            <ExampleDataSelector
              onSelect={handlePresetSelect}
              selectedId={selectedPresetId ?? undefined}
            />
            <CSVUpload
              onParsed={handleCsvParsed}
              onSampleDataGenerated={handleSampleDataGenerated}
              disabled={mutation.isPending}
            />
          </div>

          <div className="space-y-8 lg:col-span-2">
            <AnimatePresence mode="wait">
              {mutation.isPending && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center justify-center rounded-xl border border-slate-200 bg-white py-16 shadow-md dark:border-slate-700 dark:bg-slate-800"
                >
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Analyzing your finances...
                    </p>
                  </div>
                </motion.div>
              )}

              {mutation.isError && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-900/20"
                >
                  <AlertCircle className="h-6 w-6 shrink-0 text-rose-500" />
                  <p className="text-sm text-rose-700 dark:text-rose-400">
                    {getAgentErrorMessage(mutation.error)}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            {!mutation.isPending && (
              <>
                <SummaryBanner
                  monthlyIncome={income}
                  monthlyExpenses={expenses}
                  savingsRate={savingsRate}
                  hasData={hasData}
                />

                {hasResponse && response.analysis && response.analysis.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      Risk Analysis
                    </h2>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {response.analysis.map((finding, i) => (
                        <RiskCard
                          key={`${finding.dimension}-${i}`}
                          finding={finding}
                          highlighted={highlightedDimension === finding.dimension}
                          onMouseEnter={() =>
                            setHighlightedDimension(finding.dimension)
                          }
                          onMouseLeave={() => setHighlightedDimension(null)}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}

                <div className="grid gap-6 sm:grid-cols-2">
                  <SavingsGauge
                    savingsRate={savingsRate}
                    highlighted={isSavingsHighlighted}
                  />
                  <ExpenseChart
                    monthlyIncome={income}
                    monthlyExpenses={expenses}
                    highlighted={isExpenseHighlighted}
                  />
                </div>

                <MonthlyTrendChart
                  monthlyIncome={income}
                  monthlyExpenses={expenses}
                  monthlyData={monthlyData}
                  highlighted={isTrendHighlighted}
                />

                <AIReflectionPanel
                  response={response ?? null}
                  hasRun={mutation.isSuccess || mutation.isError}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
