"""Tests for tools/education.py."""

from tools.education import get_education, get_education_for_findings
from tools.rules import RuleFinding


def test_missing_education_key():
    """Non-existent dimension returns empty string."""
    assert get_education("NonexistentDimension") == ""


def test_unknown_dimension():
    """Unknown dimension returns empty string."""
    assert get_education("Unknown") == ""


def test_empty_findings_list():
    """Empty findings returns empty dict."""
    result = get_education_for_findings([])
    assert result == {}


def test_known_dimensions_return_content():
    """Known dimensions return non-empty education content."""
    assert len(get_education("Savings")) > 0
    assert len(get_education("ExpenseRatio")) > 0
    assert len(get_education("Input")) > 0


def test_get_education_for_findings_with_known_dimensions():
    """Findings with known dimensions get education content."""
    findings = [
        RuleFinding("Savings", "high", "Savings rate below 10%"),
        RuleFinding("ExpenseRatio", "medium", "Expense ratio above 80%"),
    ]
    result = get_education_for_findings(findings)
    assert "Savings" in result
    assert "ExpenseRatio" in result
    assert len(result["Savings"]) > 0
    assert len(result["ExpenseRatio"]) > 0


def test_get_education_for_findings_unknown_dimension():
    """Unknown dimension in findings gets empty string."""
    findings = [
        RuleFinding("UnknownDim", "high", "Some reason"),
    ]
    result = get_education_for_findings(findings)
    assert "UnknownDim" in result
    assert result["UnknownDim"] == ""


def test_get_education_for_findings_deduplicates_dimensions():
    """Same dimension in multiple findings appears once."""
    findings = [
        RuleFinding("Savings", "high", "reason 1"),
        RuleFinding("Savings", "medium", "reason 2"),
    ]
    result = get_education_for_findings(findings)
    assert list(result.keys()) == ["Savings"]
