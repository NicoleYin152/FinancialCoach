"""Unit tests for agent/delta_parser.py: single and multi-line expense delta parsing."""

import pytest

from agent.delta_parser import parse_expense_delta, parse_expense_deltas, parse_user_confirmation


def test_parse_expense_delta_single():
    """Single line parses to one ExpenseDelta."""
    d = parse_expense_delta("Transport +1500")
    assert d is not None
    assert d.category == "Transport"
    assert d.monthly_delta == 1500


def test_parse_expense_delta_negative():
    """Negative delta parses."""
    d = parse_expense_delta("Dining -500")
    assert d is not None
    assert d.category == "Dining"
    assert d.monthly_delta == -500


def test_parse_expense_deltas_multiline():
    """Multi-line input parses to list of ExpenseDeltas."""
    text = "Transport +1500\nDining +500"
    result = parse_expense_deltas(text)
    assert len(result) == 2
    assert result[0].category == "Transport" and result[0].monthly_delta == 1500
    assert result[1].category == "Dining" and result[1].monthly_delta == 500


def test_parse_expense_deltas_skips_invalid_lines():
    """Invalid lines are skipped; valid lines are collected."""
    text = "Transport +1500\nnot valid\nDining +500\n"
    result = parse_expense_deltas(text)
    assert len(result) == 2
    assert result[0].category == "Transport"
    assert result[1].category == "Dining"


def test_parse_expense_deltas_empty_returns_empty_list():
    """Empty or all-invalid input returns empty list."""
    assert parse_expense_deltas("") == []
    assert parse_expense_deltas("  \n  \n") == []
    assert parse_expense_deltas("foo bar\nbaz") == []


def test_parse_user_confirmation_expense_delta_single_line():
    """expense_delta schema: single line returns single ExpenseDelta."""
    parsed = parse_user_confirmation("Transport +1500", "expense_delta")
    assert parsed is not None
    assert not isinstance(parsed, list)
    assert parsed.category == "Transport" and parsed.monthly_delta == 1500


def test_parse_user_confirmation_expense_delta_multi_line():
    """expense_delta schema: multi-line returns List[ExpenseDelta]."""
    parsed = parse_user_confirmation("Transport +1500\nDining +500", "expense_delta")
    assert parsed is not None
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0].category == "Transport" and parsed[0].monthly_delta == 1500
    assert parsed[1].category == "Dining" and parsed[1].monthly_delta == 500


def test_parse_user_confirmation_expense_delta_empty_returns_none():
    """expense_delta schema: no valid deltas returns None."""
    assert parse_user_confirmation("", "expense_delta") is None
    assert parse_user_confirmation("nope", "expense_delta") is None
