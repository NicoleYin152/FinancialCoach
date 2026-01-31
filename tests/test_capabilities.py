"""Tests for agent/capabilities.py."""

import pytest

from agent.capabilities import Capabilities


def test_missing_capability_defaults_to_false():
    """Missing capabilities in dict should default to False."""
    caps = Capabilities.from_api_input({}, api_key="dummy-key")
    assert caps.llm is False
    assert caps.retry is False
    assert caps.fallback is False


def test_missing_capabilities_dict_treated_as_empty():
    """None or missing dict should default all to False."""
    caps = Capabilities.from_api_input(None, api_key="dummy-key")
    assert caps.llm is False
    assert caps.retry is False
    assert caps.fallback is False


def test_llm_disabled_when_api_key_not_present():
    """LLM must be False when OPENAI_API_KEY is not set, even if requested."""
    caps = Capabilities.from_api_input(
        {"llm": True, "retry": True, "fallback": True},
        api_key=None,
    )
    assert caps.llm is False
    assert caps.retry is True
    assert caps.fallback is True


def test_llm_disabled_when_api_key_empty():
    """LLM must be False when API key is empty string."""
    caps = Capabilities.from_api_input(
        {"llm": True},
        api_key="",
    )
    assert caps.llm is False


def test_llm_enabled_when_api_key_present():
    """LLM can be True when API key is present and requested."""
    caps = Capabilities.from_api_input(
        {"llm": True},
        api_key="sk-valid-key",
    )
    assert caps.llm is True


def test_capabilities_are_read_only():
    """Capabilities should be immutable (frozen dataclass)."""
    caps = Capabilities(llm=True, retry=True, fallback=False)
    with pytest.raises(AttributeError):
        caps.llm = False  # type: ignore
