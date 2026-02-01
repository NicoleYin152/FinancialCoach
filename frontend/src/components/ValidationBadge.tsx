import { motion } from "framer-motion";
import { CheckCircle2, XCircle } from "lucide-react";

interface ValidationBadgeProps {
  valid: boolean;
  issues?: string[];
}

export function ValidationBadge({ valid, issues = [] }: ValidationBadgeProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-1"
    >
      <div
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ${
          valid
            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
            : "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300"
        }`}
      >
        {valid ? (
          <>
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            Valid
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 shrink-0" />
            Invalid
          </>
        )}
      </div>
      {!valid && issues.length > 0 && (
        <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-rose-600 dark:text-rose-400">
          {issues.map((issue, i) => (
            <li key={i}>{issue}</li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}
