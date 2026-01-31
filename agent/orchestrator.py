"""Orchestrator: coordinates tools and enforces execution order."""

from typing import Any, Dict, List

from agent.agent import produce_response
from agent.capabilities import Capabilities
from agent.config import get_openai_api_key
from tools.education import get_education_for_findings
from tools.llm import LLMDisabledResult, generate
from tools.retry import retry_with_backoff
from tools.rules import RuleFinding, evaluate
from tools.validation import ValidationResult, validate_output


def _validate_input(input_data: Dict[str, Any]) -> List[str]:
    """Validate API input. Returns list of error strings, empty if valid."""
    errors: List[str] = []
    income = input_data.get("monthly_income")
    expenses = input_data.get("monthly_expenses")

    if income is None:
        errors.append("monthly_income is required")
    else:
        try:
            inc = float(income)
            if inc <= 0:
                errors.append("monthly_income must be positive")
        except (TypeError, ValueError):
            errors.append("monthly_income must be a valid number")

    if expenses is None:
        errors.append("monthly_expenses is required")
    else:
        try:
            exp = float(expenses)
            if exp < 0:
                errors.append("monthly_expenses must be non-negative")
        except (TypeError, ValueError):
            errors.append("monthly_expenses must be a valid number")

    return errors


def _findings_to_str(findings: List[RuleFinding]) -> str:
    """Serialize findings for LLM context."""
    return "\n".join(
        f"- {f.dimension}: {f.risk_level} - {f.reason}" for f in findings
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
    Returns structured response with analysis, education, generation, validation, errors.
    """
    errors: List[str] = []
    analysis: List[Dict[str, str]] = []
    education: Dict[str, str] = {}
    generation = ""
    validation_result: ValidationResult = ValidationResult(valid=True, issues=[])
    trace: List[str] = []

    # 1. Validate input
    input_errors = _validate_input(input_data)
    if input_errors:
        trace.append("input_validation_failed")
        return {
            "analysis": [],
            "education": {},
            "generation": "",
            "validation": {"valid": False, "issues": input_errors},
            "errors": input_errors,
            "trace": trace,
        }

    trace.append("input_validated")

    # 2. Run rules
    findings = evaluate(input_data)
    analysis = [
        {"dimension": f.dimension, "risk_level": f.risk_level, "reason": f.reason}
        for f in findings
    ]

    trace.append("rules_executed")

    # 3. Fetch education
    education = get_education_for_findings(findings)
    trace.append("education_fetched")

    # 4–6. LLM (if enabled), validate, retry/fallback
    llm_output: str | None = None
    key = api_key if api_key is not None else get_openai_api_key()

    if capabilities.llm and key:
        trace.append("llm_executed")
        findings_str = _findings_to_str(findings)
        education_str = _education_to_str(education)

        def _llm_and_validate() -> str:
            result = generate(findings_str, education_str, capabilities, api_key=key)
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
        trace.append("llm_skipped")

    # 7. Produce final response
    final = produce_response(findings, education, llm_output)
    generation = final

    trace.append("response_produced")

    return {
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
