"""Custom exceptions for the agent system."""


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class LLMDisabledError(Exception):
    """Raised when LLM is disabled or unavailable."""

    pass


class LLMProviderError(Exception):
    """Raised when LLM provider fails."""

    pass


class RetryExhaustedError(Exception):
    """Raised when all retries have been exhausted."""

    pass
