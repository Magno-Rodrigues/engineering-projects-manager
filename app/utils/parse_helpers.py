"""Shared parsing utilities for route handlers."""
from datetime import datetime
from typing import Optional


def parse_date(date_str: Optional[str]):
    """Parse a date string (YYYY-MM-DD) into a date object or return None.

    Args:
        date_str: Date string in format YYYY-MM-DD or None.

    Returns:
        datetime.date object or None if the string is empty or invalid.

    Example:
        >>> parse_date('2024-01-15')
        datetime.date(2024, 1, 15)
        >>> parse_date(None)

        >>> parse_date('invalid')

    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
