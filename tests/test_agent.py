"""Tests for agent/agent.py."""

from agent.agent import produce_response
from tools.rules import RuleFinding


def test_uses_llm_output_when_present():
    """When llm_output is present and non-empty, use it."""
    findings = [RuleFinding("Savings", "high", "Below 10%")]
    education = {"Savings": "Some education"}
    llm = "This is the LLM-generated summary."
    result = produce_response(findings, education, llm_output=llm)
    assert result == "This is the LLM-generated summary."


def test_deterministic_fallback_without_llm():
    """Without LLM output, produce deterministic concatenation."""
    findings = [
        RuleFinding("Savings", "high", "Savings rate below 10%"),
        RuleFinding("ExpenseRatio", "medium", "Expense ratio above 80%"),
    ]
    education = {
        "Savings": "Save more.",
        "ExpenseRatio": "Spend less.",
    }
    result = produce_response(findings, education, llm_output=None)
    assert "Analysis:" in result
    assert "Savings" in result
    assert "high" in result
    assert "Education:" in result
    assert "Save more" in result


def test_empty_llm_output_uses_fallback():
    """Empty or whitespace llm_output triggers fallback."""
    findings = [RuleFinding("Savings", "medium", "Below 20%")]
    education = {"Savings": "Content"}
    result = produce_response(findings, education, llm_output="   ")
    assert "Analysis:" in result
    assert "Education:" in result


def test_empty_findings_and_education():
    """Empty inputs produce fallback message."""
    result = produce_response([], {}, llm_output=None)
    assert "metrics" in result or "risk" in result.lower()


def test_invalid_findings_excluded_from_analysis_section():
    """Invalid risk findings are not listed in analysis section."""
    findings = [
        RuleFinding("Input", "invalid", "Zero or negative income"),
    ]
    education = {"Input": "Provide valid input."}
    result = produce_response(findings, education, llm_output=None)
    assert "Education:" in result
    # Invalid finding's reason is skipped (no "Zero or negative income" in analysis)
    assert "Zero or negative income" not in result
