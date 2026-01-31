"""Agent logic: produces final response from tool outputs. Does not call tools."""

from typing import Dict, List, Optional

from tools.rules import RuleFinding


def produce_response(
    findings: List[RuleFinding],
    education: Dict[str, str],
    llm_output: Optional[str] = None,
) -> str:
    """
    Produce final response from findings, education, and optional LLM output.
    Agent does NOT call tools; receives all data as arguments.
    Pure function, no state mutation.
    """
    if llm_output and llm_output.strip():
        return llm_output.strip()

    # Deterministic fallback: concatenate findings + education
    parts: List[str] = []

    if findings:
        parts.append("Analysis:")
        for f in findings:
            if f.risk_level != "invalid":
                parts.append(f"  - {f.dimension}: {f.risk_level} risk - {f.reason}")
        parts.append("")

    if education:
        parts.append("Education:")
        for dim, content in education.items():
            if content:
                parts.append(f"  {dim}: {content}")
        parts.append("")

    if not parts:
        return (
            "Your financial metrics are within typical guidelines. "
            "No specific risk areas were identified at this time."
        )

    return "\n".join(parts).strip()
