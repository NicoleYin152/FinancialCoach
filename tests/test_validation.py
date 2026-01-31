"""Tests for tools/validation.py."""

import pytest

from tools.validation import ValidationResult, validate_output


def test_invalid_language_detected():
    """Prohibited phrases result in valid=False and issues listed."""
    result = validate_output("You should invest in stocks.")
    assert result.valid is False
    assert len(result.issues) >= 1
    assert any("should" in i.lower() or "invest" in i.lower() for i in result.issues)


def test_prohibited_buy():
    """'Buy' is prohibited."""
    result = validate_output("Consider whether to buy bonds.")
    assert result.valid is False
    assert any("buy" in i.lower() for i in result.issues)


def test_prohibited_sell():
    """'Sell' is prohibited."""
    result = validate_output("You might want to sell your assets.")
    assert result.valid is False


def test_empty_output_invalid():
    """Empty output is invalid."""
    assert validate_output("").valid is False
    assert validate_output("   ").valid is False
    result = validate_output("")
    assert "empty" in result.issues[0].lower()


def test_valid_content_passes():
    """Valid content with no prohibited language passes."""
    result = validate_output(
        "Based on your savings rate, consider reflecting on your spending patterns. "
        "What areas might you explore for improvement?"
    )
    assert result.valid is True
    assert len(result.issues) == 0


def test_valid_reflective_questions():
    """Reflective questions without advice pass."""
    result = validate_output(
        "What patterns do you notice in your expenses? "
        "How do you feel about your current savings rate?"
    )
    assert result.valid is True
