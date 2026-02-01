# Demo Alignment Verification Report

**Source of truth:** 6-minute demo behavior.  
**Scope:** Verification only; no refactor.

---

## Checklist: Demo Guarantees

### 1. Intent ownership

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| LLM decides user intent (baseline / scenario / clarification / explanation) | **PASS** (when `agent: true`) | `agent/action_planner.py` 187–211: when `api_key` is set, LLM returns JSON parsed into `AgentAction`; `parsed.type` is one of `run_analysis`, `explain_previous`, `compare_scenarios`, `clarifying_question`, `noop`. |
| Frontend does not infer intent from text | **PASS** | `frontend/src/components/ChatPanel.tsx` 249–261: `sendMessage` sends `message` and `input` to `chatAgent()`; no parsing of message to choose endpoint or intent. |
| Backend routes logic based only on planner-returned intent | **PASS** | `agent/action_executor.py` 46–93: `execute()` branches strictly on `action.type`; no alternate path from message content. |

**Note:** When `capabilities.agent: false` (e.g. ChatPanel sends `agent: false`), intent is decided by **backend** deterministic heuristics (`_default_action`, `_has_ambiguous_intent`, `_wants_analysis`, `_has_structured_delta`) in `agent/action_planner.py` 303–324 — not by the frontend. So “LLM decides” holds when the demo runs with `agent: true`.

---

### 2. Baseline vs scenario

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| Baseline financial state is created once and is immutable | **PASS** | `agent/schemas/conversation.py` 51–56: `baseline_input` field. `agent/conversation_orchestrator.py` 78–88: `baseline_input` and `last_input_snapshot` are set only when `action.type == "run_analysis"`; when `action.type == "compare_scenarios"` they are **not** updated (comment: "Do NOT update baseline_input or last_input_snapshot"). |
| Scenario is always computed as delta on top of baseline | **PASS** | `agent/action_executor.py` 162, 196, 216–217, 235: `baseline_input = state.baseline_input or state.last_input_snapshot or input_data`; `ctx_baseline = FinancialContext.from_api_input(baseline_input)`; `ctx_scenario = ctx_baseline.apply_expense_delta(...)` (or `apply_expense_deltas`); `scenario_input = ctx_scenario.to_api_input()`. |
| Applying a scenario must NEVER mutate baseline state | **PASS** | Same as above: orchestrator never assigns to `baseline_input` or `last_input_snapshot` on `compare_scenarios`. Executor only reads baseline; scenario is a new context. |
| Multiple scenarios must always re-start from baseline | **PASS** | Executor always uses `state.baseline_input or state.last_input_snapshot or input_data` for baseline (line 162); no use of previous scenario output as input. |

**Clone behavior:** `tools/context.py` 110–133: `apply_expense_delta` returns a **new** `FinancialContext` instance; it does not mutate `self`. No shared mutable reference between baseline and scenario.

---

### 3. Clarifying questions

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| If category or amount is missing, planner triggers clarifying intent | **PASS** | `agent/action_planner.py` 145–158: when `_has_valid_categories(effective_input)` is false and `_wants_analysis(msg)`, returns `clarifying_question` with `expected_schema: "expense_categories"`. 166–185: when `_has_ambiguous_intent(msg)` and no `_has_structured_delta(msg)`, returns `clarifying_question` with `expected_schema: "expense_delta"`. Executor 65–67: when `_input_incomplete(input_data)` on run_analysis, returns clarifying message and ui_blocks. |
| Backend returns a structured clarifying schema (category + amount rows) | **PASS** | `agent/action_executor.py` 346–372: `_ui_blocks_for_clarification` returns editor blocks with `editorType: "financial_input"` (income + category table) or `"expense_categories"` (delta rows) or `"asset_allocation"`; initial categories use `value: {}` (empty). |
| UI only renders the schema; it does not guess categories from text | **PASS** | Backend sends `value: {}` for initial categories (line 358). Frontend `ExpenseCategoryEditor` receives rows from `block.value`; `PREDEFINED_CATEGORIES` is a **datalist** for autocomplete only (`frontend/src/components/ExpenseCategoryEditor.tsx` 4–12, 84–88), not pre-filled category names from frontend logic. |

---

### 4. Tool usage

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| Financial calculations are done only in deterministic tools | **PASS** | `tools/registry.py` 16–27: tools are `InputValidationTool`, `ExpenseRatioTool`, `ExpenseConcentrationTool`, `AssetConcentrationTool`, `LiquidityTool`. `tools/expense_ratio_tool.py` 16–62: pure logic on `ctx.derived_metrics`; thresholds and severity; no prompts. |
| Tools do not call LLMs | **PASS** | No `openai`, `generate`, or `explain` in `tools/expense_ratio_tool.py`, `tools/expense_concentration_tool.py`, `tools/asset_concentration_tool.py`, `tools/liquidity_tool.py`, `tools/input_validation_tool.py`. LLM lives in `tools/llm.py` and is invoked from `agent/orchestrator.py` (narrative) and `agent/action_executor.py` (explain_previous text), not from inside tool `run()`. |
| Same input → same output (pure functions) | **PASS** | Tools take `FinancialContext` and return `list[ToolResult]`; no I/O or randomness in tool implementations. |

---

### 5. Explanation mode

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| “Explain” uses existing results only | **PASS** | `agent/action_executor.py` 95–130: `explain_previous` reads `RUN_HISTORY[state.last_run_id]`, builds `results_str` from `memory.tool_results`, calls `explain_results(results_str, last_user, api_key)` for narrative. No `run()` or `run_tools()` call. |
| No recomputation, no new tool calls during explanation | **PASS** | Same path: only `explain_results` (LLM for explanation text); no analysis or scenario execution. |

---

### 6. Frontend responsibility

| Guarantee | Result | Evidence |
|-----------|--------|----------|
| Frontend never invents meaning | **PASS** | ChatPanel displays `response.assistant_message`, `response.ui_blocks`, `response.analysis`; message type from `response.message_type`. No local derivation of intent or risk from message text. |
| Risk level, savings rate, concentration flags are backend-decided | **PASS** | Analysis rows come from backend (`response.analysis` with `dimension`, `risk_level`, `reason`). Charts use `ui_blocks` data (`savingsRate`, `monthlyIncome`, `monthlyExpenses`) from backend. `RiskCard` uses `finding.risk_level` from backend (`frontend/src/components/RiskCard.tsx` 20, 52). |
| UI only renders backend responses | **PASS** | ChatPanel 268–276: appends assistant message with `content: response.assistant_message`, `uiBlocks: response.ui_blocks`, `analysis: response.analysis`. Table/chart blocks render `block.data` / `block.rows`. |

---

## A–F Codebase Checks

### A. LLM → Intent

- **Intent field:** `agent/schemas/action.py` 9–15: `ActionType` = `run_analysis` | `explain_previous` | `compare_scenarios` | `clarifying_question` | `noop`. `AgentAction.type` is the single intent.
- **Parsing:** `agent/action_planner.py` 218–220: `parsed = AgentAction.model_validate_json(json_str)`; type normalized to one of the five at 202.
- **Routing:** `agent/action_executor.py` 46–93: strict `if action.type == ...`; no branch on message text.
- **Frontend/regex deciding behavior:** None. Frontend sends message + input; backend uses planner output only. When LLM is off, backend uses keyword heuristics (e.g. `_has_ambiguous_intent`, `_wants_analysis`) in the planner, not in the executor.

### B. State isolation

- **Baseline state:** `agent/schemas/conversation.py` 51–56: `baseline_input`.
- **Scenario computation:** `agent/action_executor.py` 196, 216: `ctx_baseline = FinancialContext.from_api_input(baseline_input)`; then `ctx_scenario = ctx_baseline.apply_expense_delta(...)`. `tools/context.py` 110–133: `apply_expense_delta` returns a new `FinancialContext`.
- **No scenario write-back:** `agent/conversation_orchestrator.py` 85–88: on `compare_scenarios`, only `last_run_type = "scenario"`; comment and code confirm no update to `baseline_input` or `last_input_snapshot`.
- **Shared mutable references:** None; context is cloned per scenario.

### C. Clarifying flow

- **Missing info → clarify intent:** Planner 145–158 (need categories), 166–185 (ambiguous scenario); executor 65–67 (incomplete input on run_analysis).
- **Initial category rows from backend:** Executor 355–359 sends `value: {}` for initial categories; frontend shows empty form (one empty row by UI convention in FinancialInputEditor).
- **Hard-coded category guessing:** Backend does not send default category names. Frontend `PREDEFINED_CATEGORIES` is a datalist for suggestions only.

### D. Tool purity

- **No prompt logic in tools:** Confirmed for expense_ratio, expense_concentration, asset_concentration, liquidity, input_validation.
- **No LLM calls inside tools:** Grep: no `openai`/`generate`/`explain` in those tool files.
- **Deterministic:** Same context in → same ToolResults out.

### E. Explanation path

- **No analysis/scenario recomputation:** `explain_previous` only reads `RUN_HISTORY` and calls `explain_results` (narrative).
- **Cached results only:** Uses `memory.tool_results` from stored run.

### F. Documentation alignment

- **README:** Describes chat-first flow, action schema, clarification retry, “baseline vs scenario diff” (line 94, 164). Does not explicitly state “baseline is immutable” or “scenario never mutates baseline”; code enforces both.
- **Capabilities in docs vs code:** README “LLM planner decides the next action” and “LLMs are optional” match planner behavior (LLM when agent=true, fallback when false). No capability claimed in docs is missing in code.
- **Behavior in code not in docs:** Baseline immutability and `baseline_input`/`last_run_type` are implemented but not called out in README; eval mentions “baseline vs scenario diff” (README 164). DOCUMENTATION.md does not detail baseline immutability.

---

## Alignment summary

**Verdict: Aligned with demo guarantees.**

All six demo guarantees have a **PASS** in code and behavior. The only conditional is intent ownership when **LLM is off**: then intent is decided by backend heuristics (keyword/regex), not the LLM — but the frontend still does not infer intent, and the backend still routes only on planner output.

**Top 3 risks that could break the demo (if someone changed code):**

1. **Baseline mutation:** If orchestrator or executor ever set `state.baseline_input` or `state.last_input_snapshot` after a `compare_scenarios` run (e.g. from `input_data` that contained scenario payload), baseline would drift. Current code explicitly avoids this in `conversation_orchestrator.py` 85–88.
2. **Using scenario as next baseline:** If `_execute_compare_scenarios` used `scenario_input` or any “last run” scenario as the baseline for a subsequent scenario, metrics would stack. Current code uses only `state.baseline_input or state.last_input_snapshot or input_data` for baseline (line 162).
3. **Frontend inferring intent:** If the frontend ever chose different API calls or payloads based on parsing the user message (e.g. “analyze” → /agent/run, “what if” → different body), intent would no longer be owned by the backend/LLM. Current ChatPanel only sends `message` + `input` to `/agent/chat` with fixed capabilities.

---

## Exact file references (for audit)

| Check | File | Line(s) |
|-------|------|--------|
| LLM intent parsing | `agent/action_planner.py` | 187–211, 218–220 |
| Intent enum / routing | `agent/schemas/action.py` | 9–15, 21–29; `agent/action_executor.py` | 46–93 |
| Baseline state definition | `agent/schemas/conversation.py` | 51–56 |
| Baseline set only on run_analysis | `agent/conversation_orchestrator.py` | 78–88 |
| Scenario from baseline only | `agent/action_executor.py` | 162, 196, 216–217, 235 |
| Context clone (no mutate) | `tools/context.py` | 110–133, 136–140 |
| Clarifying schema (empty initial) | `agent/action_executor.py` | 346–372, 358 |
| Tools no LLM | `tools/expense_ratio_tool.py`, `tools/registry.py` | (whole files) |
| Explain cached only | `agent/action_executor.py` | 95–130 |
| Frontend no intent | `frontend/src/components/ChatPanel.tsx` | 249–261, 268–276 |
| Risk from backend | `frontend/src/components/RiskCard.tsx` | 20, 52 |
