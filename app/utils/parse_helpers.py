"""Shared parsing helpers used across route modules."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a date string (YYYY-MM-DD) into a date object or return None.

    Args:
        date_str: Date string in format YYYY-MM-DD or None.

    Returns:
        datetime.date object, or None if the input is absent or invalid.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Parse a string or number into a Decimal or return a default value.

    Args:
        value: Value to convert (string, int, float, or None).
        default: Value to return when conversion fails. Defaults to None.

    Returns:
        Decimal, or *default* if the input is absent or invalid.
    """
    if value is None or value == '':
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default
