"""LLM provider with capability gating and fallback stub."""

from dataclasses import dataclass
from typing import Union

from agent.capabilities import Capabilities
from agent.config import get_openai_api_key


@dataclass
class LLMDisabledResult:
    """Indicates LLM was not invoked; orchestrator uses deterministic path."""

    pass


FALLBACK_STUB_MESSAGE = (
    "Based on the analysis provided, consider reflecting on your financial patterns. "
    "What patterns do you notice? What would you like to explore further?"
)


def _build_safe_prompt(findings_str: str, education_str: str) -> str:
    """
    Build a prompt that restricts LLM to: summarize, paraphrase, reflective questions.
    No advice language.
    """
    return (
        "You are a financial education assistant. Do NOT give advice, recommendations, "
        "or prescriptions. Only summarize, paraphrase, or ask reflective questions.\n\n"
        f"Findings:\n{findings_str}\n\n"
        f"Education content:\n{education_str}\n\n"
        "Provide a brief summary and 1-2 reflective questions. "
        "Use only the information above. Do not add new facts."
    )


def generate(
    findings_str: str,
    education_str: str,
    capabilities: Capabilities,
    api_key: Union[str, None] = None,
) -> Union[str, LLMDisabledResult]:
    """
    Generate LLM output. Returns LLMDisabledResult if disabled or no API key.
    Provider order: OpenAI first, then fallback stub on failure.
    """
    if not capabilities.llm:
        return LLMDisabledResult()

    key = api_key if api_key is not None else get_openai_api_key()
    if not key or not key.strip():
        return LLMDisabledResult()

    prompt = _build_safe_prompt(findings_str, education_str)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        content = response.choices[0].message.content
        return content.strip() if content else FALLBACK_STUB_MESSAGE
    except Exception:
        if capabilities.fallback:
            return FALLBACK_STUB_MESSAGE
        raise


def _build_explain_prompt(results_str: str, user_question: str) -> str:
    """Build prompt for explain_result. No advice language."""
    return (
        "You are a financial education assistant. Do NOT give advice, recommendations, "
        "or predictions. Only explain what the analysis shows in plain language.\n\n"
        f"Analysis results:\n{results_str}\n\n"
        f"User asked: {user_question}\n\n"
        "Explain the relevant findings in 2-4 sentences. Use only the information above."
    )


def explain_results(
    results_str: str,
    user_question: str,
    api_key: str | None,
) -> str:
    """
    Use LLM to explain existing ToolResults in response to user question.
    Returns fallback message if LLM disabled or fails.
    """
    if not api_key or not api_key.strip():
        return (
            "I can explain the analysis. Please ensure the API is configured "
            "for explanation features."
        )

    try:
        from openai import OpenAI

        prompt = _build_explain_prompt(results_str, user_question)
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        content = response.choices[0].message.content
        return content.strip() if content else FALLBACK_STUB_MESSAGE
    except Exception:
        return FALLBACK_STUB_MESSAGE
