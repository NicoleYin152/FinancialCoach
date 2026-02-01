import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { FileSpreadsheet, Upload, X, AlertCircle, Sparkles } from "lucide-react";
import { parseCsvToFinancials } from "../utils/csvParser";
import { generateSamplePortfolioData } from "../utils/sampleDataGenerator";
import type { MonthlyDataPoint } from "../utils/sampleDataGenerator";
import type { FinancialInput } from "./InputPanel";

interface CSVUploadProps {
  onParsed: (input: Partial<FinancialInput>) => void;
  onSampleDataGenerated?: (monthlyData: MonthlyDataPoint[]) => void;
  disabled?: boolean;
}

export function CSVUpload({
  onParsed,
  onSampleDataGenerated,
  disabled = false,
}: CSVUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) {
        setFileName(null);
        setError(null);
        return;
      }
      setError(null);
      const reader = new FileReader();
      reader.onload = () => {
        const text = reader.result as string;
        const result = parseCsvToFinancials(text);
        if (result.success) {
          setFileName(file.name);
          const data: Partial<FinancialInput> = {
            monthly_income: String(result.data.monthly_income.toFixed(2)),
            monthly_expenses: String(result.data.monthly_expenses.toFixed(2)),
          };
          onParsed(data);
        } else {
          setError(result.error);
          setFileName(null);
        }
      };
      reader.onerror = () => setError("Failed to read file");
      reader.readAsText(file);
    },
    [onParsed]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith(".csv")) {
      handleFile(file);
    } else {
      setError("Please upload a CSV file");
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => setDragOver(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    handleFile(file ?? null);
  };

  const clear = () => {
    handleFile(null);
  };

  const handleGenerateSample = () => {
    if (disabled) return;
    const { monthlyData, avgIncome, avgExpenses } = generateSamplePortfolioData();
    onParsed({
      monthly_income: String(avgIncome.toFixed(2)),
      monthly_expenses: String(avgExpenses.toFixed(2)),
    });
    onSampleDataGenerated?.(monthlyData);
    setFileName(null);
    setError(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-md dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="mb-4 flex items-center gap-2">
        <FileSpreadsheet className="h-5 w-5 text-slate-500" />
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Portfolio Data (CSV)
        </h2>
      </div>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
        Don't have data? Generate a realistic sample portfolio to explore
        insights.
      </p>
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`relative rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          dragOver && !disabled
            ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/20"
            : "border-slate-300 dark:border-slate-600"
        } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
      >
        <input
          type="file"
          accept=".csv"
          onChange={onInputChange}
          disabled={disabled}
          className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
        />
        {fileName ? (
          <div className="flex items-center justify-center gap-2">
            <Upload className="h-8 w-8 text-emerald-500" />
            <span className="font-medium text-emerald-700 dark:text-emerald-400">
              {fileName}
            </span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                clear();
              }}
              className="rounded p-1 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600"
              aria-label="Remove file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="mx-auto mb-2 h-10 w-10 text-slate-400" />
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Drop CSV here or click to browse
            </p>
          </>
        )}
      </div>
      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-rose-600 dark:text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      <motion.button
        type="button"
        whileHover={!disabled ? { scale: 1.02 } : {}}
        whileTap={!disabled ? { scale: 0.97 } : {}}
        onClick={handleGenerateSample}
        disabled={disabled}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        <Sparkles className="h-4 w-4" />
        Generate Sample Portfolio Data
      </motion.button>
    </motion.div>
  );
}
