"""Tests for tools/retry.py."""

from unittest.mock import patch

import pytest

from tools.retry import retry_with_backoff


def test_retry_count_respected():
    """Retries up to max_retries + 1 total attempts."""
    call_count = 0

    def failing_fn():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("fail")

    with patch("tools.retry.time.sleep"):
        with pytest.raises(ConnectionError):
            retry_with_backoff(
                failing_fn, max_retries=3, retriable_errors=(ConnectionError,)
            )

    assert call_count == 4  # initial + 3 retries


def test_succeeds_on_first_try():
    """No retries when first call succeeds."""
    call_count = 0

    def ok_fn():
        nonlocal call_count
        call_count += 1
        return 42

    result = retry_with_backoff(ok_fn, max_retries=3, retriable_errors=(ConnectionError,))
    assert result == 42
    assert call_count == 1


def test_non_retriable_error_exits_immediately():
    """Non-retriable error: single attempt, no retry."""
    call_count = 0

    def bad_fn():
        nonlocal call_count
        call_count += 1
        raise ValueError("not retriable")

    with pytest.raises(ValueError):
        retry_with_backoff(
            bad_fn,
            max_retries=3,
            retriable_errors=(ConnectionError, TimeoutError),
        )

    assert call_count == 1


def test_backoff_timing():
    """Backoff delays increase exponentially."""
    call_count = 0
    delays = []

    def failing_fn():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("fail")

    with patch("tools.retry.time.sleep") as mock_sleep:
        mock_sleep.side_effect = lambda d: delays.append(d)
        with pytest.raises(ConnectionError):
            retry_with_backoff(
                failing_fn,
                max_retries=3,
                retriable_errors=(ConnectionError,),
                backoff_base=1.0,
            )

    # After attempt 1 fail: sleep 1
    # After attempt 2 fail: sleep 2
    # After attempt 3 fail: sleep 4
    assert delays == [1.0, 2.0, 4.0]
    assert call_count == 4


def test_succeeds_after_retries():
    """Succeeds on third attempt after two failures."""
    call_count = 0

    def eventually_ok_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("fail")
        return "success"

    with patch("tools.retry.time.sleep"):
        result = retry_with_backoff(
            eventually_ok_fn,
            max_retries=3,
            retriable_errors=(ConnectionError,),
        )
    assert result == "success"
    assert call_count == 3
