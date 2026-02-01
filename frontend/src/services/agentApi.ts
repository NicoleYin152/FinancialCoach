import axios, { AxiosError } from "axios";

// Empty string uses same origin; Vite proxy forwards /agent to backend in dev
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export interface ExpenseCategory {
  category: string;
  amount: number;
}

export interface AssetAllocation {
  asset_class: string;
  allocation_pct: number;
}

export interface AgentInput {
  monthly_income: number;
  monthly_expenses?: number;
  expense_categories?: ExpenseCategory[];
  asset_allocation?: AssetAllocation[];
  current_savings?: number;
  risk_tolerance?: string;
}

export interface AnalysisItem {
  dimension: string;
  risk_level: string;
  reason: string;
}

export interface TraceInfo {
  tools_executed?: string[];
  metrics_computed?: string[];
  context_snapshot?: Record<string, unknown>;
  phases?: string[];
}

export interface AgentResponse {
  analysis: AnalysisItem[];
  education: Record<string, string>;
  generation: string;
  validation: { valid: boolean; issues: string[] };
  errors: string[];
  trace: string[] | TraceInfo;
}

const client = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export async function runAgent(input: AgentInput): Promise<AgentResponse> {
  const payload: Record<string, unknown> = {
    monthly_income: input.monthly_income,
    ...(input.current_savings != null && { current_savings: input.current_savings }),
    ...(input.risk_tolerance && { risk_tolerance: input.risk_tolerance }),
  };
  if (input.expense_categories && input.expense_categories.length > 0) {
    payload.expense_categories = input.expense_categories;
    if (input.monthly_expenses != null) {
      payload.monthly_expenses = input.monthly_expenses;
    }
  } else if (input.monthly_expenses != null) {
    payload.monthly_expenses = input.monthly_expenses;
  }
  if (input.asset_allocation && input.asset_allocation.length > 0) {
    payload.asset_allocation = input.asset_allocation;
  }
  const { data } = await client.post<AgentResponse>("/agent/run", {
    input: payload,
    capabilities: { llm: false, retry: false, fallback: false },
  });
  return data;
}

export function isAgentError(err: unknown): err is AxiosError {
  return axios.isAxiosError(err);
}

export function getAgentErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === "ERR_NETWORK") {
      return "Unable to reach the server. Make sure the backend is running.";
    }
    const msg = err.response?.data?.detail;
    if (typeof msg === "string") return msg;
    if (Array.isArray(msg)) {
      return msg.map((m: { msg?: string }) => m?.msg ?? JSON.stringify(m)).join("; ");
    }
    if (msg && typeof msg === "object") {
      return (msg as { message?: string }).message ?? JSON.stringify(msg);
    }
    return err.message || "Request failed";
  }
  return err instanceof Error ? err.message : "An unexpected error occurred";
}
