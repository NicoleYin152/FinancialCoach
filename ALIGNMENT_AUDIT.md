# Repo & Documentation Alignment Audit

**Task:** Verification / Alignment Audit (no refactor, no new features)  
**Source of truth:** Demo guarantees (ground truth)

---

## 1. Checklist Table

| # | Guarantee | PASS / FAIL | Evidence (file + line) |
|---|-----------|-------------|------------------------|
| 1 | **Intent ownership:** User intent (analysis / scenario / clarification / explanation) is decided by the backend agent (LLM when enabled, deterministic fallback otherwise). | **PASS** | Backend: `agent/action_planner.py` 191–215 (LLM path returns `AgentAction`), 303–324 (`_default_action` when no LLM). Intent is never derived in the frontend. |
| 2 | **Intent ownership:** Frontend does not infer or route intent from user text. | **PASS** | `frontend/src/components/ChatPanel.tsx` 249–261: `sendMessage` forwards `message` and `input` to `chatAgent()`; no parsing of message to choose endpoint or intent. |
| 3 | **Baseline vs scenario:** Baseline financial input is immutable. | **PASS** | `agent/conversation_orchestrator.py` 77–88: `baseline_input` and `last_input_snapshot` are set only when `action.type == "run_analysis"`; on `compare_scenarios` they are explicitly not updated (comment: "Do NOT update baseline_input or last_input_snapshot"). |
| 4 | **Baseline vs scenario:** Scenario analysis is always a delta applied on the baseline. | **PASS** | `agent/action_executor.py` 162, 196, 216–217, 235: baseline from `state.baseline_input or state.last_input_snapshot or input_data`; `ctx_baseline = FinancialContext.from_api_input(baseline_input)`; `ctx_scenario = ctx_baseline.apply_expense_delta(...)` (or `apply_expense_deltas`); `scenario_input = ctx_scenario.to_api_input()`. |
| 5 | **Baseline vs scenario:** Scenario execution never mutates baseline. Multiple scenarios always start from the same baseline. | **PASS** | Same as #3; executor always uses baseline from state (line 162), never previous scenario. `tools/context.py` 110–133: `apply_expense_delta` returns a new `FinancialContext`; no mutation of `self`. |
| 6 | **Clarifying questions:** Missing category or amount triggers a clarifying action. | **PASS** | `agent/action_planner.py` 145–158 (no valid categories + wants analysis → `clarifying_question` with `expected_schema: "expense_categories"`), 166–185 (ambiguous intent, no structured delta → `clarifying_question` with `expected_schema: "expense_delta"`). `agent/action_executor.py` 65–67: `run_analysis` with `_input_incomplete(input_data)` returns clarifying message and ui_blocks. |
| 7 | **Clarifying questions:** Backend returns structured schemas (category + amount rows). Frontend only renders schemas; it does not guess or auto-fill meaning. | **PASS** | Backend: `agent/action_executor.py` 346–372: `_ui_blocks_for_clarification` returns editor blocks with `editorType` and `value`; for need_initial_categories sends `value: {}` (line 356). Frontend: `ExpenseCategoryEditor.tsx` 4–12, 84–88: `PREDEFINED_CATEGORIES` used only as datalist for autocomplete; row data from `block.value` (backend). |
| 8 | **Tool usage:** All financial calculations are performed in deterministic tools. Tools never call LLMs. Same input → same output. | **PASS** | `tools/registry.py` 16–27: tools are `InputValidationTool`, `ExpenseRatioTool`, etc. No `openai`/`generate`/`explain` in `tools/expense_ratio_tool.py`, `expense_concentration_tool.py`, `asset_concentration_tool.py`, `liquidity_tool.py`, `input_validation_tool.py`. LLM lives in `tools/llm.py` and is invoked from `agent/orchestrator.py` and `agent/action_executor.py` (explain_previous), not from inside tool `run()`. |
| 9 | **Explanation mode:** "Explain" reuses existing results only. No recomputation or tool execution during explanation. | **PASS** | `agent/action_executor.py` 95–130: `explain_previous` reads `RUN_HISTORY[state.last_run_id]`, builds `results_str` from `memory.tool_results`, calls `explain_results(...)` for narrative only; no `run()` or `run_tools()`. |
| 10 | **Frontend responsibility:** Frontend never invents meaning. Risk levels, savings rates, and flags come exclusively from backend responses. UI only renders backend-provided messages and UI blocks. | **PASS** | ChatPanel 268–276: appends assistant message with `content: response.assistant_message`, `uiBlocks: response.ui_blocks`, `analysis: response.analysis`. ChartBlock 121–124: `savingsRate` from `block.data`. TableBlock 216–220: rows from `block.rows`; RiskCard uses `finding.risk_level`/`finding.dimension` from backend (`frontend/src/components/RiskCard.tsx` 20, 52). On API error, only exception/network message is shown; no fabricated risk or savings. |

---

## 2. Alignment Summary

**Verdict: Fully aligned.**

All listed demo guarantees are enforced in code. Intent is owned by the backend (LLM when `capabilities.agent` and API key are set, otherwise deterministic heuristics in the planner); the frontend never infers or routes on message content. Baseline is set only on `run_analysis` and is never updated by `compare_scenarios`; scenario is always computed as a delta on that baseline. Clarification flow and schemas are backend-driven; the frontend renders backend-provided `ui_blocks` and does not guess categories or amounts. Tools are deterministic and do not call LLMs. Explain uses cached run results only. The UI displays only backend-supplied messages, analysis rows, and chart/editor blocks.

**README / DOCUMENTATION vs code**

- **Claims reflected in code:** Chat-first flow, action schema (run_analysis / explain_previous / compare_scenarios / clarifying_question / noop), clarification retry (at most 2 attempts then noop with trace), baseline vs scenario diff, executor branching only on planner action type, no generic assistant fallback from executor, frontend rendering only backend content—all match the implementation.
- **Enforced in code but not stated in docs:** README and DOCUMENTATION.md do not explicitly state that "baseline is immutable" or "scenario never mutates baseline." The behavior is enforced in `conversation_orchestrator.py` (78–88) and described in `ConversationState` in `agent/schemas/conversation.py` (51–56). This is a documentation gap, not a behavioral mismatch.
- **No claim in docs that is violated by code.** No change to code behavior recommended; doc clarification optional.

---

## 3. Risk Notes (hypothetical future-breakage risks)

1. **Baseline mutation:** If the orchestrator or executor ever set `state.baseline_input` or `state.last_input_snapshot` after a `compare_scenarios` run (e.g. from `input_data` that included scenario payload), the baseline would drift and multiple scenarios would no longer start from the same baseline. Current code explicitly avoids this in `agent/conversation_orchestrator.py` 85–88.

2. **Using scenario as next baseline:** If `_execute_compare_scenarios` (or any caller) used `scenario_input` or the last scenario run as the baseline for a subsequent scenario, metrics would stack. Current code uses only `state.baseline_input or state.last_input_snapshot or input_data` for baseline (`agent/action_executor.py` 162).

3. **Frontend inferring intent:** If the frontend ever chose different API calls or payloads based on parsing the user message (e.g. "analyze" → `/agent/run`, "what if" → different body or capabilities), intent would no longer be owned solely by the backend/LLM. Current ChatPanel only sends `message` + `input` + fixed capabilities to `/agent/chat`.

---

*Audit completed against demo guarantees; no refactors or feature proposals.*
