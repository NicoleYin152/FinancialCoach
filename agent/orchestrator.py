"""Orchestrator: coordinates tools and enforces execution order."""

import time
import uuid
from typing import Any, Dict, List

from agent.agent import produce_response
from agent.memory import RUN_HISTORY, RunMemory
from agent.capabilities import Capabilities
from agent.config import get_openai_api_key
from agent.planner import select_tools
from tools.context import FinancialContext
from tools.education import get_education_for_results
from tools.llm import LLMDisabledResult, generate
from tools.registry import run_tools
from tools.retry import retry_with_backoff
from tools.schemas import ToolResult
from tools.validation import ValidationResult, validate_output


def _validate_input(input_data: Dict[str, Any]) -> List[str]:
    """Validate API input. Returns list of error strings, empty if valid."""
    errors: List[str] = []
    income = input_data.get("monthly_income")
    expenses = input_data.get("monthly_expenses")
    expense_categories = input_data.get("expense_categories")
    asset_allocation = input_data.get("asset_allocation")

    if income is None:
        errors.append("monthly_income is required")
    else:
        try:
            inc = float(income)
            if inc <= 0:
                errors.append("monthly_income must be positive")
        except (TypeError, ValueError):
            errors.append("monthly_income must be a valid number")

    has_expenses = expenses is not None
    has_categories = expense_categories and len(expense_categories) > 0
    if not has_expenses and not has_categories:
        errors.append("Either monthly_expenses or expense_categories (non-empty) is required")
    elif has_expenses:
        try:
            exp = float(expenses)
            if exp < 0:
                errors.append("monthly_expenses must be non-negative")
        except (TypeError, ValueError):
            errors.append("monthly_expenses must be a valid number")
    elif has_categories:
        for i, cat in enumerate(expense_categories):
            if isinstance(cat, dict):
                amt = cat.get("amount")
                cname = cat.get("category", "")
                if not cname or not cname.strip():
                    errors.append(f"Row {i + 1}: category cannot be empty")
                try:
                    a = float(amt) if amt is not None else 0
                    if a < 0:
                        errors.append(f"Row {i + 1}: amount must be non-negative")
                except (TypeError, ValueError):
                    errors.append(f"Row {i + 1}: amount must be a valid number")

    if asset_allocation and len(asset_allocation) > 0:
        alloc_total = 0.0
        for i, a in enumerate(asset_allocation):
            if isinstance(a, dict):
                pct = a.get("allocation_pct", 0)
                try:
                    p = float(pct)
                    if p < 0 or p > 100:
                        errors.append(f"Asset {i + 1}: allocation_pct must be 0-100")
                    alloc_total += p
                except (TypeError, ValueError):
                    errors.append(f"Asset {i + 1}: allocation_pct must be a valid number")
        if abs(alloc_total - 100) > 0.1:
            errors.append(f"asset_allocation percentages must sum to 100 (got {alloc_total})")

    return errors


def _results_to_str(results: List[ToolResult]) -> str:
    """Serialize tool results for LLM context."""
    return "\n".join(
        f"- {r.dimension}: {r.severity} - {r.reason}" for r in results
    )


def _education_to_str(education: Dict[str, str]) -> str:
    """Serialize education for LLM context."""
    return "\n".join(f"{k}: {v}" for k, v in education.items() if v)


def run(
    input_data: Dict[str, Any],
    capabilities: Capabilities,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """
    Execute the agent pipeline. Never crashes silently.
    Returns structured response with analysis, education, generation, validation, errors, trace.
    """
    errors: List[str] = []
    analysis: List[Dict[str, Any]] = []
    education: Dict[str, str] = {}
    generation = ""
    validation_result: ValidationResult = ValidationResult(valid=True, issues=[])
    trace: Dict[str, Any] = {
        "planner_used": False,
        "planner_status": "skipped",
        "tools_selected": [],
        "tools_executed": [],
        "context_snapshot": {},
    }

    # 1. Validate input
    input_errors = _validate_input(input_data)
    if input_errors:
        trace["phases"] = ["input_validation_failed"]
        return {
            "run_id": None,
            "analysis": [],
            "education": {},
            "generation": "",
            "validation": {"valid": False, "issues": input_errors},
            "errors": input_errors,
            "trace": trace,
        }

    # 1b. Normalize: compute monthly_expenses from expense_categories if needed
    normalized = dict(input_data)
    if normalized.get("monthly_expenses") is None and normalized.get("expense_categories"):
        cats = normalized["expense_categories"]
        total = sum(
            float(c.get("amount", 0) or 0)
            for c in cats
            if isinstance(c, dict)
        )
        normalized["monthly_expenses"] = total

    # 2. Build FinancialContext (single source of truth)
    try:
        ctx = FinancialContext.from_api_input(normalized)
    except Exception as e:
        trace["phases"] = ["context_build_failed"]
        return {
            "run_id": None,
            "analysis": [],
            "education": {},
            "generation": "",
            "validation": {"valid": False, "issues": [str(e)]},
            "errors": [str(e)],
            "trace": trace,
        }

    trace["context_snapshot"] = ctx.to_snapshot()

    # 3. Select tools (planner or fallback)
    key = api_key if api_key is not None else get_openai_api_key()
    selected_tools = select_tools(ctx, capabilities.agent, key, trace)

    # 4. Run tools
    results, tools_executed, metrics_computed = run_tools(ctx, selected_tools)
    trace["tools_executed"] = tools_executed
    trace["metrics_computed"] = metrics_computed
    trace["phases"] = ["input_validated", "tools_executed", "education_fetched"]

    # 5. Build analysis (backward compat: risk_level = severity, supporting_metrics = metrics)
    analysis = [
        {
            "dimension": r.dimension,
            "risk_level": r.severity,
            "reason": r.reason,
            "supporting_metrics": r.metrics,
        }
        for r in results
    ]

    # 6. Fetch education per dimension
    education = get_education_for_results(results)

    # 7–9. LLM (if enabled), validate, retry/fallback
    llm_output: str | None = None

    if capabilities.llm and key:
        trace["phases"].append("llm_executed")
        results_str = _results_to_str(results)
        education_str = _education_to_str(education)

        def _llm_and_validate() -> str:
            result = generate(results_str, education_str, capabilities, api_key=key)
            if isinstance(result, LLMDisabledResult):
                return ""
            return result

        def _try_llm() -> tuple[str, ValidationResult]:
            out = _llm_and_validate()
            if not out:
                return "", ValidationResult(valid=True, issues=[])
            vr = validate_output(out)
            return out, vr

        def _attempt() -> str:
            out, vr = _try_llm()
            if out and vr.valid:
                return out
            if not out:
                return ""
            raise ValueError("Validation failed")

        if capabilities.retry:
            try:
                llm_output = retry_with_backoff(
                    _attempt,
                    max_retries=2,
                    retriable_errors=(ValueError,),
                )
            except ValueError:
                llm_output = None
            except Exception as e:
                errors.append(str(e))
                llm_output = None
        else:
            out, vr = _try_llm()
            if vr.valid:
                llm_output = out
            else:
                validation_result = vr
                if capabilities.fallback:
                    llm_output = None
                else:
                    errors.extend(vr.issues)
    else:
        trace["phases"].append("llm_skipped")

    # 10. Produce final response
    from tools.rules import RuleFinding

    findings = [
        RuleFinding(dimension=r.dimension, risk_level=r.severity, reason=r.reason)
        for r in results
    ]
    final = produce_response(findings, education, llm_output)
    generation = final

    trace["phases"].append("response_produced")

    # Store run memory for replay/debug (in-memory only)
    run_id = uuid.uuid4().hex
    RUN_HISTORY[run_id] = RunMemory(
        run_id=run_id,
        context_snapshot=trace["context_snapshot"],
        tools_selected=selected_tools,
        tool_results=[r.model_dump() for r in results],
        timestamp=time.time(),
    )

    return {
        "run_id": run_id,
        "analysis": analysis,
        "education": education,
        "generation": generation,
        "validation": {
            "valid": validation_result.valid,
            "issues": validation_result.issues,
        },
        "errors": errors,
        "trace": trace,
    }
