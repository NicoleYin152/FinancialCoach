"""Tests for tools/llm.py."""

from unittest.mock import patch

import pytest

from agent.capabilities import Capabilities
from tools.llm import (
    LLMDisabledResult,
    FALLBACK_STUB_MESSAGE,
    generate,
)


def test_no_api_key_returns_llm_disabled_result():
    """When API key is missing, returns LLMDisabledResult."""
    caps = Capabilities(llm=True, retry=False, fallback=True)
    with patch("tools.llm.get_openai_api_key", return_value=None):
        result = generate("findings", "education", caps)
    assert isinstance(result, LLMDisabledResult)


def test_llm_disabled_capability_returns_llm_disabled_result():
    """When capabilities.llm is False, returns LLMDisabledResult."""
    caps = Capabilities(llm=False, retry=False, fallback=True)
    result = generate("findings", "education", caps, api_key="sk-fake")
    assert isinstance(result, LLMDisabledResult)


def test_provider_failure_with_fallback_returns_stub():
    """When provider fails and fallback enabled, returns stub message."""
    caps = Capabilities(llm=True, retry=False, fallback=True)
    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API error")
        result = generate("findings", "education", caps, api_key="sk-fake")
    assert result == FALLBACK_STUB_MESSAGE


def test_provider_failure_without_fallback_raises():
    """When provider fails and fallback disabled, raises."""
    caps = Capabilities(llm=True, retry=False, fallback=False)
    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API error")
        with pytest.raises(Exception):
            generate("findings", "education", caps, api_key="sk-fake")


def test_prompt_safety_no_advice_language():
    """Generated prompts must not contain prescriptive advice language."""
    from tools.llm import _build_safe_prompt

    prompt = _build_safe_prompt("Some findings", "Some education")
    forbidden = ["you should", "buy", "sell", "invest in"]
    prompt_lower = prompt.lower()
    for phrase in forbidden:
        assert phrase not in prompt_lower, f"Prompt contains forbidden phrase: {phrase}"


def test_prompt_includes_restriction():
    """Prompt must instruct model not to give advice."""
    from tools.llm import _build_safe_prompt

    prompt = _build_safe_prompt("findings", "education")
    assert "do not" in prompt.lower() or "do not give" in prompt.lower()
