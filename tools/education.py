"""Static education content lookup for rule dimensions."""

from typing import Dict, List

from tools.rules import RuleFinding


_EDUCATION_MAP: Dict[str, str] = {
    "Savings": (
        "Building savings is important for financial security. "
        "Experts generally recommend saving at least 20% of income when possible. "
        "A higher savings rate provides a larger buffer for unexpected expenses."
    ),
    "ExpenseRatio": (
        "Your expense ratio shows what portion of income goes to expenses. "
        "Keeping expenses below 80% of income leaves room for savings and emergencies. "
        "Tracking expenses can help identify areas to adjust."
    ),
    "Input": (
        "Valid financial input requires positive income and non-negative expenses. "
        "Please provide accurate monthly income and expense figures."
    ),
}


def get_education(dimension: str) -> str:
    """
    Get static education content for a dimension.
    Returns empty string if dimension is unknown.
    """
    return _EDUCATION_MAP.get(dimension, "")


def get_education_for_findings(findings: List[RuleFinding]) -> Dict[str, str]:
    """
    Map each finding's dimension to its education content.
    Unknown dimensions yield empty string.
    Returns empty dict if findings list is empty.
    """
    result: Dict[str, str] = {}
    for finding in findings:
        dim = finding.dimension
        if dim not in result:
            result[dim] = get_education(dim)
    return result
