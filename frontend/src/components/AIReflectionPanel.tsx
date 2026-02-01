import { motion } from "framer-motion";
import { Bot, Zap, ZapOff } from "lucide-react";
import { ValidationBadge } from "./ValidationBadge";
import type { AgentResponse } from "../services/agentApi";

interface AIReflectionPanelProps {
  response: AgentResponse | null;
  hasRun?: boolean;
}

export function AIReflectionPanel({
  response,
  hasRun = false,
}: AIReflectionPanelProps) {
  if (!hasRun) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-600 dark:bg-slate-800/50"
      >
        <Bot className="mx-auto mb-2 h-10 w-10 text-slate-400" />
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Run analysis to see AI insight summary
        </p>
      </motion.div>
    );
  }

  if (!response) return null;

  const llmUsed = response.trace?.includes("llm_executed") ?? false;
  const llmSkipped = response.trace?.includes("llm_skipped") ?? false;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-md dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-slate-500" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            AI Insight Summary
          </h3>
        </div>
        <div className="flex items-center gap-3">
          {llmUsed && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
              <Zap className="h-3.5 w-3.5" />
              LLM used
            </span>
          )}
          {llmSkipped && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-300">
              <ZapOff className="h-3.5 w-3.5" />
              Deterministic Mode (No AI used)
            </span>
          )}
          <ValidationBadge
            valid={response.validation.valid}
            issues={response.validation.issues}
          />
        </div>
      </div>
      {response.generation ? (
        <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-700 dark:bg-slate-900/50 dark:text-slate-300">
          <p className="whitespace-pre-wrap">{response.generation}</p>
        </div>
      ) : (
        <p className="text-sm italic text-slate-500 dark:text-slate-400">
          No generated content (deterministic output only)
        </p>
      )}
      {response.errors && response.errors.length > 0 && (
        <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-900/20 dark:text-rose-400">
          {response.errors.map((err, i) => (
            <p key={i}>{err}</p>
          ))}
        </div>
      )}
    </motion.div>
  );
}
