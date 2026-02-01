# Smart Financial Coach

A capability-gated, agent-orchestrated system that demonstrates **secure AI integration** for decision-adjacent applications. The financial domain is used as a representative example; the focus is on orchestration patterns, not feature richness.

## What This System Demonstrates

- **Chat-first agent** — Chat is the only user surface; the LLM planner decides the next action; deterministic tools do the computation.
- **Secure agent orchestration** — One agent + orchestrator + tools; no multi-agent systems.
- **Capability-gated LLM usage** — LLMs are optional; the system runs fully without them.
- **Graceful degradation** — Deterministic logic always produces output; LLM failures trigger noop (no silent heuristic fallback).
- **Trust boundaries** — Deterministic rules and validation; LLMs never override rule outcomes.
- **Clarification retry policy** — At most 2 clarification attempts per unresolved intent; then a minimal noop message.

## How to Run Locally

### One-command run

```bash
uvicorn api.server:app --reload
```

Then use the **chat** endpoint (primary surface):

```bash
curl -X POST http://127.0.0.1:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"t1","message":"Analyze my finances","input":{"monthly_income":8000,"monthly_expenses":5500},"capabilities":{"llm":false,"agent":false}}'
```

Or the **single-run** endpoint (unchanged behavior):

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": {"monthly_income": 8000, "monthly_expenses": 5500}, "capabilities": {"llm": false}}'
```

### Dependencies

```bash
pip install -r requirements.txt
```

### Frontend

From the project root:

```bash
cd frontend && npm install && npm run dev
```

Backend must be running on `http://127.0.0.1:8000` (Vite proxies `/agent` to it). See [DOCUMENTATION.md](DOCUMENTATION.md) section 13 for frontend details.

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /agent/chat` | Multi-turn chat. Send a message and optional financial input; returns `assistant_message`, `run_id`, `analysis`, `trace`, `message_type`, `ui_blocks`. Primary user surface. |
| `POST /agent/run` | Single analysis run. Same as before: validate input, run tools, return analysis, education, generation, validation, trace. |
| `GET /agent/replay/{run_id}` | Debug: return stored `RunMemory` for a given `run_id`. |

## How to Enable LLM

1. Create a `.env` file in the project root (do not commit it).
2. Add your OpenAI API key: `OPENAI_API_KEY=sk-your-key-here`.
3. Set `capabilities.llm: true` and `capabilities.agent: true` in your request body for chat (so the action planner uses the LLM).

Example with LLM enabled:

```bash
curl -X POST http://127.0.0.1:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Analyze my finances","input":{"monthly_income":8000,"monthly_expenses":5500},"capabilities":{"llm":true,"agent":true}}'
```

## Security Guarantees

- **No secrets in repo** — All API keys are loaded from environment variables.
- **Public, runnable** — Clone and run without embedding credentials.
- **Deterministic core** — Rules and validation are independent of LLM outputs.
- **Validated outputs** — LLM responses are checked for prohibited advice language.

## Chat Flow (Action Schema)

The planner returns a single `AgentAction` with:

- **`type`**: One of `run_analysis`, `explain_previous`, `compare_scenarios`, `clarifying_question`, `noop`.
- **`reasoning`**: Brief reasoning for the decision.
- **`parameters`**: Optional dict (e.g. `question`, `expected_schema`, `delta`).

Behavior:

- **First ambiguous input** (e.g. “What if I buy a car?”) → `clarifying_question`; assistant asks for category and amount; no tools run.
- **Valid delta after clarification** (e.g. “+1500 per month in transport”) → `compare_scenarios`; baseline vs scenario diff; tools run.
- **Clear intent** (e.g. “Analyze my finances” with input) → `run_analysis`; tools run.
- **Explain previous** → `explain_previous`; no re-run; explanation from last run.
- **Clarification retry** — At most 2 clarification attempts; on the third unresolved input, planner returns `noop` with a minimal “insufficient information” message; trace includes `clarification_attempt: 3` and `planner_decision: noop_due_to_clarification_limit`.

## Design Decisions & Non-Goals

- **No database or persistence** — Outputs are computed per request; conversation state is in-memory. Reduces attack surface and keeps the system stateless across restarts.
- **No real financial APIs** — External banking or market data is out of scope; the system uses synthetic input only to demonstrate orchestration patterns.
- **No multi-agent system** — A single agent (planner + executor) receives context; the orchestrator invokes tools based on the planner’s action type.
- **No prescriptive financial advice** — LLMs are restricted to summarization and reflective questions; validation blocks advice language such as “you should” or “buy/sell.”
- **No generic help text** — Assistant messages come only from the agent (planner/executor); the UI does not show hardcoded “I’m here to help” style fallbacks.

## Running Tests

```bash
pytest tests/ eval/ -v
```

All unit and eval tests must pass. Manual chat acceptance tests (equivalent to the four curl scenarios):

```bash
PYTHONPATH=. python scripts/manual_chat_tests.py
```

## Project Structure & Code Overview

### Execution Flow

- **Chat path**: Request → `POST /agent/chat` → `chat()` in `conversation_orchestrator` → `select_action()` in `action_planner` (LLM when enabled, else deterministic fallback) → `execute()` in `action_executor` (strict branch on `action.type`) → response with `assistant_message`, `trace`, `ui_blocks`.
- **Run path**: Request → `POST /agent/run` → `run()` in `orchestrator` → validate input → run tools (via `run_tools`) → optional LLM generation → validate output → return analysis, education, generation, trace.

The agent (planner) never invokes tools directly; the executor runs tools only for `run_analysis` and `compare_scenarios` (with delta).

### Directory Layout

- **`agent/`** — Action planner, action executor, conversation orchestrator, conversation store, delta parser, orchestrator (for `/agent/run`), agent (for final text), capabilities, config, memory, schemas (action, conversation, delta, planner).
- **`tools/`** — Deterministic tools (input_validation, expense_ratio, expense_concentration, asset_concentration, liquidity), registry, context, education, LLM (gated), validation, retry.
- **`api/`** — FastAPI app: `POST /agent/run`, `POST /agent/chat`, `GET /agent/replay/{run_id}`.
- **`eval/`** — Eval tests: chat-first flows, action schema, clarification limit, scenario diff, regression.
- **`tests/`** — Unit tests for agent, API, capabilities, education, LLM, orchestrator, retry, rules, tools, validation.
- **`scripts/`** — `manual_chat_tests.py` for the four acceptance curl-style tests.
- **`frontend/`** — React + Vite; ChatPanel is the main UI; renders backend messages and `ui_blocks` (charts, tables, editors).

### Core Files (Chat Path)

| File | Purpose |
|------|---------|
| `agent/action_planner.py` | LLM-driven (when enabled) or deterministic; returns `AgentAction`; ambiguous intent → `clarifying_question`; max 2 clarification attempts then `noop`. |
| `agent/action_executor.py` | Executes only what the planner decided; branches on `action.type`; no help-text fallback. |
| `agent/conversation_orchestrator.py` | Multi-turn chat; updates conversation state, `clarification_attempt`, `pending_clarification`; merges trace. |
| `agent/schemas/action.py` | `AgentAction` (type, reasoning, parameters); action types and expected_schema. |
| `agent/schemas/conversation.py` | `ConversationState`, `ConversationTurn`, `PendingClarification`, `clarification_attempt`. |
| `agent/delta_parser.py` | Parses user confirmation into `ExpenseDelta` or `AssetDelta`. |

### Core Files (Run Path & Shared)

| File | Purpose |
|------|---------|
| `agent/orchestrator.py` | Pipeline for `/agent/run`: validate → run tools → education → optional LLM → validate → retry/fallback. |
| `agent/agent.py` | Produces final response text from findings, education, and optional LLM output. |
| `agent/capabilities.py` | Capability flags (`llm`, `retry`, `fallback`, `agent`); LLM disabled when API key absent. |
| `agent/memory.py` | `RunMemory` and `RUN_HISTORY` for replay and explain_previous. |
| `tools/registry.py` | Tool registry; `run_tools()` runs input_validation then selected analysis tools. |
| `tools/validation.py` | Validates LLM output for prohibited language. |
| `api/server.py` | FastAPI app and request/response schemas. |

### Test Coverage

- **tests/** — Unit tests: rules, education, LLM, validation, retry, agent, orchestrator, capabilities, API.
- **eval/** — Chat-first: ambiguous → clarifying, delta → compare_scenarios, retry then noop, clarification limit (2 attempts), baseline vs scenario diff, `/agent/run` unchanged.

## Architecture

See [DOCUMENTATION.md](DOCUMENTATION.md) for the full Agent-Oriented Architecture Specification, including the chat-first flow, API details, and frontend (section 13).

## Release checklist

- [x] Chat-first flow verified
- [x] Clarification retry capped at 2 attempts
- [x] No generic assistant fallback text
- [x] Deterministic tool execution
- [x] Trace includes planner_decision and clarification_attempt
- [x] Manual chat tests pass
