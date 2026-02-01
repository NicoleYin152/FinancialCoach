# Smart Financial Coach

## Agent-Oriented Architecture Specification

### Version

v1.1 — Chat-first agent, action planner/executor, clarification retry policy.

---

## 1. Problem Statement

Modern AI-powered applications increasingly rely on Large Language Models (LLMs) to generate insights, explanations, and recommendations. However, integrating LLMs safely into decision-adjacent systems (e.g. finance, security, risk analysis) presents several challenges:

* LLM outputs are probabilistic and may hallucinate
* External APIs introduce availability, rate-limit, and security risks
* Public, runnable codebases must not embed secrets
* Systems must degrade gracefully when AI capabilities are unavailable

This project demonstrates how to design a **secure, agent-based orchestration system** that integrates LLMs responsibly while keeping deterministic logic, validation, and trust boundaries explicit.

The financial domain is used as a **representative example**, not as the core focus.

---

## 2. Design Goals

### Primary Goals

* Demonstrate **agent orchestration** rather than feature breadth
* Integrate LLMs in a **capability-gated and secure** manner
* Ensure the system is **public, runnable, and secret-free**
* Show **graceful degradation** when AI capabilities are unavailable
* Emphasize **trust, validation, and error handling**

### Non-Goals (Explicitly Out of Scope)

* User accounts, authentication, or persistence
* Real financial data ingestion or banking APIs
* Production-grade databases or RAG infrastructure
* Prescriptive financial advice or automated actions

---

## 3. High-Level Architecture Overview

The system is structured as a **set of independently degradable agents** coordinated by a central orchestrator.

```
┌──────────────────────┐
│  Agent Orchestrator  │
└─────────┬────────────┘
          │
 ┌────────┼───────────────┐
 │        │               │
 ▼        ▼               ▼
Rule   Education       Validation
Agent    Agent           Agent
 │        │               │
 └────────┼──────┬────────┘
          ▼      ▼
       LLM Augmentation
        (Optional)
```

Key architectural principle:

> **No single agent is required for system execution.
> All agents degrade independently based on capability availability.**

### 3.1 Chat-First User Surface

The **primary user surface** is multi-turn chat (`POST /agent/chat`). The flow is:

1. **Action planner** (LLM when enabled, else deterministic) decides the next action and returns a single `AgentAction` with `type`, `reasoning`, and `parameters`.
2. **Action executor** runs only what the planner decided: `run_analysis`, `explain_previous`, `compare_scenarios`, `clarifying_question`, or `noop`. No executor-side intent guessing or generic help-text fallback.
3. **Clarifying questions** are first-class: ambiguous intents (e.g. “What if I buy a car?”) produce `clarifying_question`; no tools run until the user provides a structured delta (e.g. “+1500 per month in transport”) or valid analysis input.
4. **Clarification retry policy**: At most **2 clarification attempts** per unresolved intent. On the third ambiguous/unparseable input, the planner returns `noop` with a minimal “insufficient information” message; trace includes `clarification_attempt: 3` and `planner_decision: noop_due_to_clarification_limit`. The counter resets when a non-clarifying action succeeds (`run_analysis`, `compare_scenarios`, `explain_previous`).

The single-run endpoint `POST /agent/run` is unchanged: it runs the pipeline once and returns analysis, education, generation, and trace.

---

## 4. Agent Responsibilities

### 4.1 Rule Agent

* Performs deterministic financial risk analysis
* Uses a small, hardcoded ruleset (intentional for scope control)
* Produces structured, explainable outputs

**Key Properties**

* Fully deterministic
* Always auditable
* LLM may *augment explanations*, but **never override rule outcomes**

Example Output:

```json
{
  "dimension": "Savings",
  "risk_level": "high",
  "reason": "Savings rate below 10%"
}
```

---

### 4.2 Education Agent

* Provides contextual financial education related to detected risks
* Uses a static, hardcoded knowledge base in v1

**Design Rationale**
Hardcoded education content is an intentional placeholder to demonstrate:

* Agent boundaries
* Interface-based extensibility
* Future replacement by RAG / vector databases

The Education Agent may optionally use LLMs to:

* Paraphrase
* Contextualize
* Adjust tone

It **must not introduce new factual claims**.

---

### 4.3 LLM Augmentation Layer

LLMs are treated as **optional capability providers**, not as authoritative decision-makers.

LLMs may be used to:

* Generate summaries
* Rephrase education content
* Produce reflective (non-prescriptive) coaching questions

LLMs are explicitly prohibited from:

* Making financial recommendations
* Introducing external knowledge
* Producing actionable instructions

---

### 4.4 Validation Agent

Any LLM-generated output passes through a validation step.

Validation checks include:

* Presence of prohibited advice language
* Hallucinated facts outside provided context
* Structural integrity of responses

Validation may be:

* Rule-based (primary)
* LLM-assisted (optional, secondary)

Invalid outputs trigger retries or graceful fallback.

---

## 5. Capability Gating & Degradation Model

Capabilities are enabled dynamically based on:

* Environment variables
* Runtime availability
* Provider health

Example capability flags:

```json
{
  "llm": true,
  "education": true,
  "retry": true,
  "fallback": true
}
```

Degradation behavior:

* If LLM unavailable → deterministic + static output
* If validation fails → retry with backoff
* If retries exhausted → best-effort output or structured error

This ensures the system **always runs**, even with zero AI access.

---

## 6. LLM Provider Strategy

The system supports **pluggable LLM providers** via a shared interface.

```python
class LLMProvider:
    def generate(prompt) -> str
```

Supported providers (v1):

* OpenAI (primary implementation)
* Anthropic / Gemini (stubs or fallback-ready)

Provider selection supports:

* Ordered fallback
* Runtime failure detection
* Configurable retry policies

---

## 7. Retry, Backoff, and Fallback

LLM calls are wrapped with:

* Exponential backoff (1s → 2s → 4s)
* Maximum retry limits (configurable)
* Provider-level fallback

Failure modes are:

* Logged
* Reported via structured error messages
* Never crash the system silently

---

## 8. API Design

The system exposes three endpoints.

### POST `/agent/chat` (primary user surface)

Multi-turn conversational agent. Request:

```json
{
  "conversation_id": "optional-existing-id",
  "message": "Analyze my finances",
  "input": {
    "monthly_income": 8000,
    "monthly_expenses": 5500
  },
  "capabilities": {
    "llm": false,
    "retry": false,
    "fallback": false,
    "agent": false
  }
}
```

Response:

```json
{
  "conversation_id": "...",
  "assistant_message": "...",
  "run_id": "uuid-or-null",
  "analysis": [...],
  "education": {...},
  "trace": {
    "planner_decision": "run_analysis",
    "action_taken": "run_analysis",
    "clarification_attempt": 0,
    ...
  },
  "message_type": "assistant",
  "ui_blocks": [...]
}
```

When the clarification limit is hit, `trace.planner_decision` is `noop_due_to_clarification_limit` and `trace.clarification_attempt` is `3`.

### POST `/agent/run`

Single analysis run. Request:

```json
{
  "input": {
    "monthly_income": 8000,
    "monthly_expenses": 5500,
    "current_savings": 15000,
    "risk_tolerance": "medium"
  },
  "capabilities": {
    "llm": true,
    "retry": true,
    "fallback": true
  },
  "llm_config": { ... }
}
```

Response:

```json
{
  "run_id": "...",
  "analysis": [...],
  "education": {...},
  "generation": "...",
  "validation": {...},
  "errors": [],
  "trace": {...}
}
```

### GET `/agent/replay/{run_id}`

Debug-only: returns stored `RunMemory` for a given `run_id` (tools executed, tool results, context snapshot, timestamp). Returns 404 if not found.

---

## 9. Security & Trust Considerations

* No API keys are stored or committed
* All secrets are injected via environment variables
* Public repository is safe to clone and run
* Deterministic logic remains independent of LLMs
* LLM outputs are validated and never blindly trusted

---

## 10. Future Extensions (Not Implemented)

* Replace static education with RAG (e.g. Weaviate)
* Persist agent outputs for longitudinal analysis
* Add multiple domain-specific agent pipelines
* Introduce model-based evaluators

---

## 11. Summary

This project focuses on **how to safely orchestrate AI agents**, not on maximizing application features.
It demonstrates a production-relevant pattern for integrating LLMs into systems that require trust, explainability, and resilience—principles central to modern security and platform engineering.

---

## 12. Agent Tooling & Capability Policy

### 12.1 Design Principle

Agents in this system do **not** have unrestricted tool access.

All tool usage follows three principles:

1. **Explicit Invocation** – tools are called only by the orchestrator, not autonomously by agents
2. **Capability Gating** – tool access depends on runtime configuration and availability
3. **Least Privilege** – agents receive only the minimum context required for their task

This design prevents uncontrolled agent behavior and aligns with security-first system design.

---

### 12.2 Supported Tool Categories (v1)

In the current implementation, agents may access the following tool categories:

#### 1. Deterministic Computation Tools

* Rule evaluation logic
* Static education lookup
* Input validation utilities

These tools are always safe, deterministic, and side-effect free.

---

#### 2. LLM Generation Tools (Optional)

LLM providers are treated as **external, untrusted services**.

LLMs may be used **only** for:

* Natural language summarization
* Educational paraphrasing
* Reflective (non-prescriptive) coaching questions

LLMs are explicitly **not allowed** to:

* Execute code
* Access external data sources
* Perform financial calculations
* Make decisions or recommendations

---

#### 3. Validation Tools

Validation tools may include:

* Rule-based validators
* Secondary LLM validators (optional)

Validation tools operate **after generation** and cannot modify upstream deterministic outputs.

---

### 12.3 Explicitly Disallowed Tools

To maintain a clear trust boundary, the following tools are **intentionally excluded** in v1:

* External web search or browsing
* Database write access
* File system mutation
* Network calls beyond configured LLM providers
* Autonomous tool selection by agents

This ensures that agents cannot introduce unverified information or side effects.

---

### 12.4 Orchestrator-Mediated Tool Access

Agents do not directly invoke tools.

* **Chat path**: The **action planner** (LLM or deterministic) returns an `AgentAction`; the **action executor** runs tools only for `run_analysis` and `compare_scenarios` (with delta). The **conversation orchestrator** manages turns, `clarification_attempt`, and `pending_clarification`.
* **Run path**: The **orchestrator** (`agent/orchestrator.py`) determines which tools are available, runs them in order, injects tool outputs as context, and handles retries and fallbacks.

This separation ensures that the planner remains a **pure reasoning component** (no tool calls), while the executor and orchestrator enforce system policy and invoke tools.

---

### 12.5 Future Extensions (Not Implemented)

Future versions may introduce additional tools, such as:

* Retrieval tools backed by vector databases (RAG)
* Persistent storage adapters
* Domain-specific calculators

All future tools would follow the same capability-gated, orchestrator-controlled model demonstrated in this project.

---

## 13. Frontend

All documentation lives in the project root. This section summarizes the frontend (React + Vite in `frontend/`).

### 13.1 Quick Start

```bash
cd frontend && npm install && npm run dev
```

Backend must be running on `http://localhost:8000`. Vite proxies `/agent` to it.

### 13.2 Primary Surface: ChatPanel

The **only** interactive user surface is **ChatPanel**. It:

- Maintains conversation state (messages, financial context) and sends the current context with each message.
- Renders **only** what the backend returns: assistant text and `ui_blocks` (charts, tables, editors). No hardcoded assistant messages (e.g. “I’m here to help”).
- Handles `message_type`: `assistant`, `clarifying_question`, `scenario_result`, `error`.

Users type messages (e.g. “Analyze my finances”, “What if I buy a car?”, “+1500 per month in transport”) and optionally use inline editors when the backend returns `ui_blocks` with `editorType: financial_input`, `expense_categories`, or `asset_allocation`.

### 13.3 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **ChatPanel** | Main page. Message list, input, rendering of `ui_blocks` (SavingsGauge, ExpenseChart, AssetAllocationChart, analysis table, FinancialInputEditor, ExpenseCategoryEditor, AssetAllocationEditor). Submits via `chatAgent()` with current financial input. |
| **FinancialInputEditor** | Inline editor for income, expenses, savings; used when backend returns `editorType: financial_input`. |
| **ExpenseCategoryEditor** | Inline editor for expense categories; used when backend asks for delta/categories. |
| **AssetAllocationEditor** | Inline editor for asset allocation; used when backend returns `editorType: asset_allocation`. |
| **SavingsGauge** | Renders savings rate from `ui_blocks` chart data. |
| **ExpenseChart** | Renders income/expense allocation from `ui_blocks`. |
| **AssetAllocationChart** | Renders asset allocation pie from `ui_blocks`. |
| **RiskCard** | Renders analysis rows (dimension, risk_level, reason) from `ui_blocks` table. |
| **Dashboard** | Re-exports or wraps ChatPanel. |
| **InputPanel** | Manual entry for income/expenses; used where standalone input is needed (e.g. presets, CSV). |
| **CSVUpload** | Drag-and-drop or file select for CSV; parses via `csvParser`. |
| **ExampleDataSelector** | Presets (Struggling, Moderate, Comfortable). |
| **SummaryBanner** | Displays income, expenses, savings rate, status badge. |
| **ValidationBadge** | Valid/invalid badge for AI output. |
| **Tooltip** | Hover tooltip for rule explanations. |

### 13.4 Services & Utils

| File | Responsibility |
|------|----------------|
| **agentApi.ts** | `chatAgent(message, conversationId?, input?, capabilities?)` POST to `/agent/chat`. Types: `AgentInput`, `ChatResponse` (assistant_message, run_id, analysis, education, trace, message_type, ui_blocks), `UIBlock`. |
| **csvParser.ts** | Parse CSV, detect income/expense columns, derive monthly averages. |
| **mappings.ts** | `DIMENSION_TO_CHART`, `RISK_COLORS`, `DIMENSION_LABELS` for RiskCard and chart highlighting. |

### 13.5 Supported CSV Formats (Frontend)

- **Format A (Monthly):** columns `month`, `income`, `expenses`.
- **Format B (Categorized):** columns `month`, `category`, `amount`; income entered manually.
- **Format C (Transaction log):** columns `month`, `type`, `amount`, `category` with `type` = income/expense.

Templates and “Generate fake sample data” are available in the UI.

### 13.6 Tech Stack & Configuration

- **Stack:** Vite, React, TypeScript, Tailwind v4, Recharts, Framer Motion, Axios, Lucide React.
- **Vite proxy:** `/agent` → `http://localhost:8000` in dev (avoids CORS).
- **VITE_API_URL:** Optional; empty uses same-origin + proxy in dev.

### 13.7 UI/UX Notes

- **Background & cards:** Gradient `from-slate-50 to-slate-100`; cards use `border-slate-200`, `shadow-md`.
- **Colors:** Primary Indigo; status Emerald (healthy), Amber (moderate), Rose (risk).
- **Charts:** Savings Gauge (gradient arc emerald/amber/rose); Income Allocation Donut (expenses rose, savings emerald); Trend Chart with rounded bars / AreaChart when monthly data available.
- **Rationale:** Fintech polish, clear hierarchy (Input → Insight → Visualization → Reflection), cohesive palette for demos.

