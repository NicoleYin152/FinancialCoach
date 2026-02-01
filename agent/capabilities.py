"""Capability model for gating LLM and retry behavior."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Capabilities:
    """Read-only capabilities. Immutable once created."""

    llm: bool = False
    retry: bool = False
    fallback: bool = False
    agent: bool = False

    @classmethod
    def from_api_input(
        cls,
        capabilities_dict: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> "Capabilities":
        """
        Create Capabilities from API input and environment.
        Missing keys default to False.
        LLM is disabled if API key is not present, regardless of input.
        agent enables planner (tool selection); requires api_key.
        """
        if capabilities_dict is None:
            capabilities_dict = {}

        llm = bool(capabilities_dict.get("llm", False))
        agent = bool(capabilities_dict.get("agent", False))
        if not api_key:
            llm = False
            agent = False

        retry = bool(capabilities_dict.get("retry", False))
        fallback = bool(capabilities_dict.get("fallback", False))

        return cls(llm=llm, retry=retry, fallback=fallback, agent=agent)
