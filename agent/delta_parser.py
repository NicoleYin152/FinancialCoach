"""Parse user confirmation into ExpenseDelta or AssetDelta. Schema-bound."""

import re
from typing import Optional, Union

from agent.schemas.delta import AssetDelta, ExpenseDelta


def _extract_number(s: str) -> Optional[float]:
    """Extract first number from string, including $ and %."""
    # Match: $1500, 1500, +1500, -500, 10%, -10%
    m = re.search(r"[\$]?\s*([+-]?\d+(?:\.\d+)?)\s*%?", s)
    if m:
        return float(m.group(1))
    return None


def parse_expense_delta(text: str) -> Optional[ExpenseDelta]:
    """
    Try to parse user text as ExpenseDelta.
    Examples: "Transport +1500", "add $1500 to Transport", "+1500 Transport"
    """
    text = text.strip()
    if not text:
        return None

    num = _extract_number(text)
    if num is None:
        return None

    # Common expense category names (partial match)
    categories = [
        "housing", "rent", "mortgage", "food", "groceries", "transport", "transportation",
        "car", "utilities", "health", "insurance", "entertainment", "shopping",
        "other", "misc", "education", "travel", "dining", "subscription",
    ]
    text_lower = text.lower()
    found_category = None
    for c in categories:
        if c in text_lower:
            found_category = c
            break

    if not found_category:
        # Try to extract a word that might be a category (before or after the number)
        # e.g. "Transport 1500" or "1500 Transport"
        parts = re.split(r"[\d\$%+-]+", text, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if len(p) >= 3 and p.lower() not in ("add", "to", "in", "for", "per", "month"):
                found_category = p.strip()
                break

    if not found_category:
        return None

    # Capitalize first letter
    category = found_category.title() if isinstance(found_category, str) else found_category
    return ExpenseDelta(category=category, monthly_delta=num)


def parse_asset_delta(text: str) -> Optional[AssetDelta]:
    """
    Try to parse user text as AssetDelta.
    Examples: "Stocks -10", "reduce Stocks by 10%", "-10 Stocks"
    """
    text = text.strip()
    if not text:
        return None

    num = _extract_number(text)
    if num is None:
        return None

    asset_classes = ["stocks", "bonds", "cash", "equities", "real estate", "other"]
    text_lower = text.lower()
    found_class = None
    for ac in asset_classes:
        if ac in text_lower:
            found_class = ac
            break

    if not found_class:
        parts = re.split(r"[\d\$%+-]+", text, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if len(p) >= 2 and p.lower() not in ("reduce", "increase", "by", "to"):
                found_class = p.strip()
                break

    if not found_class:
        return None

    asset_class = found_class.title() if isinstance(found_class, str) else found_class
    return AssetDelta(asset_class=asset_class, allocation_delta_pct=num)


def parse_user_confirmation(
    text: str,
    expected_schema: str,
) -> Optional[Union[ExpenseDelta, AssetDelta]]:
    """
    Parse user reply based on expected_schema.
    Returns delta if parse succeeds, else None.
    """
    if expected_schema in ("expense_delta", "category_adjustment"):
        return parse_expense_delta(text)
    if expected_schema == "asset_change":
        return parse_asset_delta(text)
    return None
