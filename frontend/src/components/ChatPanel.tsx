import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Loader2, Send } from "lucide-react";
import { chatAgent } from "../services/agentApi";
import type { AgentInput, ChatResponse, UIBlock } from "../services/agentApi";
import { normalizeCategory } from "../utils/mappings";
import type { ExpenseCategoryRow } from "./ExpenseCategoryEditor";
import type { AssetAllocationRow } from "./AssetAllocationEditor";
import { SavingsGauge } from "./SavingsGauge";
import { ExpenseChart } from "./ExpenseChart";
import { AssetAllocationChart } from "./AssetAllocationChart";
import { RiskCard } from "./RiskCard";
import { ExpenseCategoryEditor } from "./ExpenseCategoryEditor";
import { AssetAllocationEditor } from "./AssetAllocationEditor";
import { FinancialInputEditor } from "./FinancialInputEditor";

export type ChatMessage =
  | { role: "user"; type: "text"; content: string }
  | {
      role: "assistant";
      type: "text" | "clarifying_question" | "scenario_result" | "error";
      content: string;
      uiBlocks?: UIBlock[];
      analysis?: ChatResponse["analysis"];
    };

interface ChatPanelProps {
  disabled?: boolean;
}

function getBubbleStyles(messageType?: string) {
  switch (messageType) {
    case "clarifying_question":
      return "border-2 border-indigo-300 bg-indigo-50 dark:border-indigo-600 dark:bg-indigo-950/50";
    case "scenario_result":
      return "border border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950/30";
    case "error":
      return "border border-rose-200 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/30";
    default:
      return "border border-slate-200 bg-slate-50 dark:border-slate-600 dark:bg-slate-700";
  }
}

/** Build a parseable delta message for the backend (e.g. "Transport +1500" or "Transport +1500\nDining -200"). */
function buildDeltaMessage(rows: ExpenseCategoryRow[]): string {
  return rows
    .filter((r) => r.category?.trim() && !Number.isNaN(Number.parseFloat(r.amount)))
    .map((r) => {
      const category = normalizeCategory(r.category);
      const amount = Number.parseFloat(r.amount) || 0;
      const sign = amount >= 0 ? "+" : "";
      return `${category} ${sign}${amount}`;
    })
    .join("\n");
}

/** Build a parseable asset-delta message for the backend (e.g. "Stocks -10" or "Stocks 50 Bonds 50"). */
function buildAssetDeltaMessage(rows: AssetAllocationRow[]): string {
  return rows
    .filter((r) => r.asset_class?.trim() && !Number.isNaN(Number.parseFloat(r.allocation_pct)))
    .map((r) => {
      const assetClass = r.asset_class.trim();
      const pct = Number.parseFloat(r.allocation_pct) || 0;
      return `${assetClass} ${pct}`;
    })
    .join("\n");
}

function toAgentInputFromValues(
  income: string,
  expenses: string,
  categories?: ExpenseCategoryRow[],
  allocation?: AssetAllocationRow[],
  savings?: string
): AgentInput | null {
  const monthly_income = Number.parseFloat(income) || 0;
  if (monthly_income <= 0) return null;
  const categorySum =
    categories?.reduce((s, c) => s + (Number.parseFloat(c.amount) || 0), 0) ?? 0;
  const monthly_expenses =
    categorySum > 0 ? categorySum : Number.parseFloat(expenses) || 0;
  if (monthly_expenses < 0) return null;

  const agentInput: AgentInput = {
    monthly_income,
    monthly_expenses,
    ...(savings &&
      !Number.isNaN(Number.parseFloat(savings)) && {
        current_savings: Number.parseFloat(savings),
      }),
  };

  if (categories && categories.length > 0) {
    agentInput.expense_categories = categories
      .map((c) => ({
        category: normalizeCategory(c.category),
        amount: Number.parseFloat(c.amount) || 0,
      }))
      .filter((c) => c.category && c.amount > 0);
  }

  if (allocation && allocation.length > 0) {
    const total = allocation.reduce(
      (s, a) => s + (Number.parseFloat(a.allocation_pct) || 0),
      0
    );
    if (Math.abs(total - 100) < 0.1) {
      agentInput.asset_allocation = allocation.map((a) => ({
        asset_class: a.asset_class.trim(),
        allocation_pct: Number.parseFloat(a.allocation_pct) || 0,
      }));
    }
  }
  return agentInput;
}

function ChartBlock({ block }: { block: UIBlock }) {
  if (block.type !== "chart") return null;
  const { chartType, data } = block;
  if (chartType === "savings_gauge") {
    const rate = (data?.savingsRate as number) ?? 0;
    return (
      <div className="my-2 max-w-[280px]">
        <SavingsGauge savingsRate={rate} />
      </div>
    );
  }
  if (chartType === "expense_chart") {
    const income = (data?.monthlyIncome as number) ?? 0;
    const expenses = (data?.monthlyExpenses as number) ?? 0;
    return (
      <div className="my-2 max-w-[280px]">
        <ExpenseChart monthlyIncome={income} monthlyExpenses={expenses} />
      </div>
    );
  }
  if (chartType === "asset_allocation") {
    const alloc = (data?.allocation as { asset_class: string; allocation_pct: number }[]) ?? [];
    return (
      <div className="my-2 max-w-[280px]">
        <AssetAllocationChart allocation={alloc} />
      </div>
    );
  }
  return null;
}

function ExpenseCategoryEditorWithSubmit({
  initial,
  onSubmit,
  disabled,
}: {
  initial: ExpenseCategoryRow[];
  onSubmit: (categories: ExpenseCategoryRow[]) => void;
  disabled: boolean;
}) {
  const [categories, setCategories] = useState(initial);
  const total = categories.reduce((s, c) => s + (Number.parseFloat(c.amount) || 0), 0);
  return (
    <div className="space-y-2">
      <ExpenseCategoryEditor
        categories={categories}
        onChange={setCategories}
        disabled={disabled}
      />
      <button
        type="button"
        onClick={() => onSubmit(categories)}
        disabled={disabled || total <= 0}
        className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Submit
      </button>
    </div>
  );
}

function AssetAllocationEditorWithSubmit({
  initial,
  onSubmit,
  disabled,
}: {
  initial: AssetAllocationRow[];
  onSubmit: (allocation: AssetAllocationRow[]) => void;
  disabled: boolean;
}) {
  const [allocation, setAllocation] = useState(initial);
  const total = allocation.reduce(
    (s, a) => s + (Number.parseFloat(a.allocation_pct) || 0),
    0
  );
  const isValid = Math.abs(total - 100) < 0.1;
  return (
    <div className="space-y-2">
      <AssetAllocationEditor
        allocation={allocation}
        onChange={setAllocation}
        disabled={disabled}
      />
      <button
        type="button"
        onClick={() => onSubmit(allocation)}
        disabled={disabled || !isValid}
        className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Submit
      </button>
    </div>
  );
}

function TableBlock({ block }: { block: UIBlock }) {
  if (block.type !== "table") return null;
  const { schema, rows } = block;
  if (schema === "analysis") {
    const items = (rows ?? []) as { dimension: string; risk_level: string; reason: string }[];
    return (
      <div className="my-2 grid max-w-lg gap-2 sm:grid-cols-2">
        {items.map((finding, i) => (
          <RiskCard key={`${finding.dimension}-${i}`} finding={finding} />
        ))}
      </div>
    );
  }
  return null;
}

export function ChatPanel({ disabled = false }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState<{
    income: string;
    expenses: string;
    savings: string;
    categories?: ExpenseCategoryRow[];
    allocation?: AssetAllocationRow[];
  }>({ income: "", expenses: "", savings: "" });
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const sendMessage = async (
    message: string,
    input: AgentInput | null
  ) => {
      setMessages((prev) => [...prev, { role: "user", type: "text", content: message }]);
    setLoading(true);
    try {
      const response = await chatAgent({
        conversation_id: conversationId ?? undefined,
        message,
        input: input ?? undefined,
        capabilities: { llm: false, agent: false },
      });
      setConversationId(response.conversation_id);
      // Never use internal/unknown message_type; treat unknown as plain assistant text
      const knownTypes = ["clarifying_question", "scenario_result", "error"] as const;
      const safeMessageType =
        response.message_type && knownTypes.includes(response.message_type as (typeof knownTypes)[number])
          ? (response.message_type as "clarifying_question" | "scenario_result" | "error")
          : "text";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: safeMessageType,
          content: response.assistant_message,
          uiBlocks: response.ui_blocks,
          analysis: response.analysis,
        },
      ]);
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "error",
          content: errMsg,
          uiBlocks: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    const text = inputText.trim();
    if (!text || loading || disabled) return;
    setInputText("");
    const input = toAgentInputFromValues(
      context.income,
      context.expenses,
      context.categories,
      context.allocation,
      context.savings
    );
    sendMessage(text, input);
  };

  const handleEditorSubmit = (
    editorType: string,
    value: unknown,
    triggerMessage: string
  ) => {
    if (editorType === "financial_input") {
      const v = value as {
        monthly_income?: string;
        monthly_expenses?: string;
        expense_categories?: { category: string; amount: number }[];
        current_savings?: string;
      };
      const cats =
        (v.expense_categories ?? []).map((c) => ({
          category: normalizeCategory(c.category),
          amount: String(c.amount),
        }));
      const total = cats.reduce(
        (s, c) => s + (Number.parseFloat(c.amount) || 0),
        0
      );
      setContext((prev) => ({
        ...prev,
        income: v.monthly_income ?? prev.income,
        expenses: total > 0 ? String(total) : prev.expenses,
        categories: cats,
        savings: v.current_savings ?? prev.savings,
      }));
      const input = toAgentInputFromValues(
        v.monthly_income ?? "",
        String(total) || "",
        cats,
        context.allocation,
        v.current_savings
      );
      sendMessage(triggerMessage || "Please analyze my finances.", input);
    } else if (editorType === "expense_categories") {
      const cats = (value ?? []) as ExpenseCategoryRow[];
      const total = cats.reduce((s, c) => s + (Number.parseFloat(c.amount) || 0), 0);
      const normalizedCats = cats.map((c) => ({ ...c, category: normalizeCategory(c.category) }));
      setContext((prev) => ({
        ...prev,
        categories: normalizedCats,
        expenses: total > 0 ? String(total) : prev.expenses,
      }));
      const input = toAgentInputFromValues(
        context.income,
        String(total) || context.expenses,
        normalizedCats,
        context.allocation,
        context.savings
      );
      const deltaMessage = buildDeltaMessage(normalizedCats);
      if (deltaMessage.trim()) sendMessage(deltaMessage, input);
    } else if (editorType === "asset_allocation") {
      const alloc = (value ?? []) as AssetAllocationRow[];
      setContext((prev) => ({ ...prev, allocation: alloc }));
      const input = toAgentInputFromValues(
        context.income,
        context.expenses,
        context.categories,
        alloc,
        context.savings
      );
      const assetMessage = buildAssetDeltaMessage(alloc);
      if (assetMessage.trim()) sendMessage(assetMessage, input);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950">
      <header className="border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <MessageCircle className="h-6 w-6 text-indigo-500" />
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Smart Financial Coach
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Chat to analyze your finances. All inputs happen here.
            </p>
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center dark:border-slate-700 dark:bg-slate-800">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Enter your income and expense breakdown by category, then ask for analysis.
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Try: &ldquo;Analyze my finances&rdquo; — you&rsquo;ll be asked for your category table (Category | Amount).
              </p>
            </div>
          )}
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-slate-800 dark:text-slate-200 ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : getBubbleStyles(msg.type)
                  }`}
                >
                  {msg.role === "assistant" && msg.type === "clarifying_question" && (
                    <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-indigo-600 dark:text-indigo-400">
                      Clarifying question
                    </span>
                  )}
                  {msg.role === "assistant" && msg.type === "scenario_result" && (
                    <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
                      Scenario result
                    </span>
                  )}
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                  {msg.role === "assistant" &&
                    msg.uiBlocks?.map((block, bi) => (
                      <div key={bi} className="mt-3">
                        {block.type === "chart" && <ChartBlock block={block} />}
                        {block.type === "table" && <TableBlock block={block} />}
                        {block.type === "editor" && (
                          <div className="mt-2">
                            {block.editorType === "financial_input" && (
                              <FinancialInputEditor
                                value={(block.value as Record<string, string>) ?? {}}
                                onSubmit={(v) =>
                                  handleEditorSubmit(
                                    "financial_input",
                                    v,
                                    "I've entered my financial data. Please analyze."
                                  )
                                }
                                disabled={loading}
                              />
                            )}
                            {block.editorType === "expense_categories" && (
                              <ExpenseCategoryEditorWithSubmit
                                initial={
                                  ((block.value as ExpenseCategoryRow[]) ?? [
                                    { category: "", amount: "" },
                                  ]).map((r) => ({
                                    ...r,
                                    category: r.category ? normalizeCategory(r.category) : r.category,
                                  }))
                                }
                                onSubmit={(cats) =>
                                  handleEditorSubmit("expense_categories", cats, "")
                                }
                                disabled={loading}
                              />
                            )}
                            {block.editorType === "asset_allocation" && (
                              <AssetAllocationEditorWithSubmit
                                initial={(block.value as AssetAllocationRow[]) ?? []}
                                onSubmit={(alloc) =>
                                  handleEditorSubmit("asset_allocation", alloc, "")
                                }
                                disabled={loading}
                              />
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 dark:border-slate-600 dark:bg-slate-700">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Thinking...
                </span>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      <footer className="border-t border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        <div className="mx-auto flex max-w-3xl gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask about your finances..."
            disabled={loading || disabled}
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || disabled || !inputText.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </footer>
    </div>
  );
}
