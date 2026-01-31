# Smart Financial Coach

A capability-gated, agent-orchestrated system that demonstrates **secure AI integration** for decision-adjacent applications. The financial domain is used as a representative example; the focus is on orchestration patterns, not feature richness.

## What This System Demonstrates

- **Secure agent orchestration** — One agent + orchestrator + tools; no multi-agent systems
- **Capability-gated LLM usage** — LLMs are optional; the system runs fully without them
- **Graceful degradation** — Deterministic logic always produces output; LLM failures trigger fallbacks
- **Trust boundaries** — Deterministic rules and validation; LLMs never override rule outcomes

## How to Run Locally

### One-command run

```bash
uvicorn api.server:app --reload
```

Then send a request:

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": {"monthly_income": 8000, "monthly_expenses": 5500}, "capabilities": {"llm": false}}'
```

### Dependencies

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker build -t financial-coach . && docker run -p 8000:8000 financial-coach
```

## How to Enable LLM

1. Create a `.env` file in the project root (do not commit it)
2. Add your OpenAI API key: `OPENAI_API_KEY=sk-your-key-here`
3. Set `capabilities.llm: true` in your request body

Example with LLM enabled:

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": {"monthly_income": 8000, "monthly_expenses": 5500}, "capabilities": {"llm": true, "retry": true, "fallback": true}}'
```

## Security Guarantees

- **No secrets in repo** — All API keys are loaded from environment variables
- **Public, runnable** — Clone and run without embedding credentials
- **Deterministic core** — Rules and validation are independent of LLM outputs
- **Validated outputs** — LLM responses are checked for prohibited advice language

## Example Output

**Request** (LLM disabled):

```json
{
  "input": {
    "monthly_income": 5000,
    "monthly_expenses": 4500
  },
  "capabilities": { "llm": false, "retry": false, "fallback": false }
}
```

**Response**:

```json
{
  "analysis": [
    { "dimension": "Savings", "risk_level": "medium", "reason": "Savings rate below 20%" },
    { "dimension": "ExpenseRatio", "risk_level": "medium", "reason": "Expense ratio above 80%" }
  ],
  "education": {
    "Savings": "Building savings is important for financial security. Experts generally recommend saving at least 20% of income when possible. A higher savings rate provides a larger buffer for unexpected expenses.",
    "ExpenseRatio": "Your expense ratio shows what portion of income goes to expenses. Keeping expenses below 80% of income leaves room for savings and emergencies. Tracking expenses can help identify areas to adjust."
  },
  "generation": "Analysis:\n\n  - Savings: medium risk - Savings rate below 20%\n  - ExpenseRatio: medium risk - Expense ratio above 80%\n\nEducation:\n\n  Savings: Building savings is important...",
  "validation": { "valid": true, "issues": [] },
  "errors": [],
  "trace": [ "input_validated", "rules_executed", "education_fetched", "llm_skipped", "response_produced" ]
}
```

## Design Decisions & Non-Goals

- **No database or persistence** — Outputs are computed per request and not stored; reduces attack surface and keeps the system stateless.
- **No real financial APIs** — External banking or market data is out of scope; the system uses synthetic input only to demonstrate orchestration patterns.
- **No multi-agent system** — A single agent receives precomputed tool outputs from the orchestrator; agents do not autonomously invoke tools.
- **No autonomous tool usage** — The orchestrator invokes tools in a fixed order; agents cannot choose or call tools on their own.
- **No prescriptive financial advice** — LLMs are restricted to summarization and reflective questions; validation blocks advice language such as "you should" or "buy/sell."

## Running Tests

```bash
pytest tests/ -v
```

All unit tests must pass for the implementation to be considered complete.

## Project Structure & Code Overview

### Execution Flow

Requests enter via `POST /agent/run` and are handled by the API layer, which validates the payload and passes it to the orchestrator. The orchestrator enforces a fixed pipeline: validate input → run rules → fetch education → optionally call LLM (if enabled and API key present) → validate output → retry or fallback on failure → produce final response. The agent never invokes tools directly; it receives precomputed outputs from the orchestrator and returns the final text.

### Directory Layout

- **`agent/`** — Core orchestration and agent logic. Holds the orchestrator, capability model, config, and the agent that produces the final response.
- **`tools/`** — Stateless, callable modules used by the orchestrator: deterministic rules, static education lookup, LLM generation (gated), output validation, and retry/backoff.
- **`api/`** — HTTP interface. Single endpoint that validates request schema and delegates to the orchestrator.
- **`tests/`** — Unit tests aligned with each functional module; every tool and agent component has a corresponding test file.

### Core Files

| File | Purpose |
|------|---------|
| `agent/orchestrator.py` | Runs the pipeline, enforces capability gating, retries, and fallbacks; never fails silently. |
| `agent/agent.py` | Pure function that produces the final response from findings, education, and optional LLM output; no tool calls. |
| `agent/capabilities.py` | Immutable capability flags (`llm`, `retry`, `fallback`) derived from API input and env; LLM disabled when API key is absent. |
| `agent/config.py` | Loads environment variables (e.g. `OPENAI_API_KEY`) via `python-dotenv`. |
| `agent/errors.py` | Custom exceptions for validation, LLM, and retry failures. |
| `tools/rules.py` | Deterministic risk rules (savings rate, expense ratio); returns `RuleFinding` list. |
| `tools/education.py` | Static mapping from rule dimensions to education content; returns empty string for unknown keys. |
| `tools/llm.py` | Capability-gated LLM access; returns `LLMDisabledResult` when disabled, uses fallback stub on provider failure. |
| `tools/validation.py` | Validates LLM output for prohibited language and structural issues; returns `ValidationResult`. |
| `tools/retry.py` | Exponential backoff (1s → 2s → 4s) for retriable errors only. |
| `api/server.py` | FastAPI app; `POST /agent/run` validates input and returns JSON response. |

### Test Coverage

Each tool and agent module has a dedicated test file: `test_rules.py` → `rules.py`, `test_education.py` → `education.py`, `test_llm.py` → `llm.py`, `test_validation.py` → `validation.py`, `test_retry.py` → `retry.py`, `test_agent.py` → `agent.py`, `test_orchestrator.py` → `orchestrator.py`, `test_capabilities.py` → `capabilities.py`, `test_api.py` → `api/server.py`. Tests cover edge cases (zero income, boundaries, missing fields), capability gating, validation failures, retries, and end-to-end flows.

### Extensibility and Security

The structure separates orchestration from tools, so new tools (e.g. RAG-backed education) can be added without changing the agent. Capability gating ensures optional features (LLM, retry, fallback) are controlled at runtime. All secrets come from the environment; the codebase remains safe to clone and run. Deterministic rules and validation preserve trust boundaries regardless of LLM availability.

---

## Architecture

See [DOCUMENTATION.md](DOCUMENTATION.md) for the full Agent-Oriented Architecture Specification.
