"""Output validation for LLM-generated content."""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    """Result of validating LLM output."""

    valid: bool
    issues: List[str]


_PROHIBITED_PATTERNS = [
    r"\byou\s+should\b",
    r"\byou\s+must\b",
    r"\byou\s+need\s+to\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\binvest\s+in\b",
    r"\bpurchase\b",
    r"\brecommend\s+(that\s+)?you\b",
    r"\bi\s+recommend\b",
    r"\byou\s+ought\s+to\b",
]


def validate_output(content: str) -> ValidationResult:
    """
    Validate LLM output for prohibited language and structural issues.
    Returns ValidationResult with valid=True if passed, else issues list.
    """
    issues: List[str] = []

    # Structural: non-empty
    if not content or not content.strip():
        issues.append("Output is empty")
        return ValidationResult(valid=False, issues=issues)

    # Reasonable length (optional sanity check)
    if len(content.strip()) > 10000:
        issues.append("Output excessively long")

    # Prohibited language
    content_lower = content.lower()
    for pattern in _PROHIBITED_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            issues.append(f"Prohibited language detected: {pattern}")

    return ValidationResult(valid=len(issues) == 0, issues=issues)
