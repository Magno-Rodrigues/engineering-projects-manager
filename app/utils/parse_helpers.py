"""Shared parsing helper functions for routes."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Any

def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parse a date string (YYYY-MM-DD) into a date object or return None.
    
    Args:
        date_str: Date string in format YYYY-MM-DD or None
        
    Returns:
        datetime.date object or None if parsing fails
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def parse_decimal(value: Any) -> Tuple[Optional[Decimal], Optional[str]]:
    """Parse a decimal value from form input.

    Args:
        value: Value to parse (can be string, int, float, etc.)

    Returns:
        A tuple of (Decimal, None) on success or (None, error_message) on failure.
    """
    if value is None or value == '':
        return None, None
    try:
        result = Decimal(str(value))
        if result < 0:
            return None, 'Value cannot be negative.'
        return result, None
    except InvalidOperation:
        return None, 'Invalid numeric value.'

def parse_int(value: Any) -> Optional[int]:
    """Parse a string to int or return None.
    
    Args:
        value: Value to parse
        
    Returns:
        int or None if parsing fails
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def parse_float(value: Any) -> Tuple[Optional[float], Optional[str]]:
    """Parse a float value from form input.

    Args:
        value: Value to parse

    Returns:
        A tuple of (float, None) on success or (None, error_message) on failure.
    """
    if value is None or value == '':
        return None, None
    try:
        result = float(value)
        if result < 0:
            return None, 'Value cannot be negative.'
        return result, None
    except (ValueError, TypeError):
        return None, 'Invalid numeric value.'
