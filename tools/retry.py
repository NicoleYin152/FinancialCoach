"""Retry with exponential backoff for retriable errors."""

import time
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")

# Default retriable errors: rate limit, connection, timeouts
DEFAULT_RETRIABLE_ERRORS: Tuple[type, ...] = (
    Exception,  # Plan says RateLimitError, ConnectionError - use broader set
)

# More specific: openai.RateLimitError may not exist in all versions
try:
    from openai import RateLimitError as OpenAIRateLimitError
    _RETRIABLE = (OpenAIRateLimitError, ConnectionError, TimeoutError)
except ImportError:
    _RETRIABLE = (ConnectionError, TimeoutError, OSError)


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    retriable_errors: Tuple[type, ...] = _RETRIABLE,
    backoff_base: float = 1.0,
) -> T:
    """
    Execute fn with exponential backoff on retriable errors.
    Backoff: 1s, 2s, 4s (base * 2^attempt).
    Non-retriable errors exit immediately without retry.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retriable_errors as e:
            last_error = e
            if attempt < max_retries:
                delay = backoff_base * (2**attempt)
                time.sleep(delay)
            else:
                raise
        except Exception as e:
            # Non-retriable: exit immediately
            raise
    raise last_error  # type: ignore
