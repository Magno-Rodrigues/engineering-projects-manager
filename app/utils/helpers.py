"""Helper utilities for the application."""
from datetime import datetime
from typing import Optional


def format_date(date: Optional[datetime], fmt: str = '%d/%m/%Y') -> str:
    """Format a date object to a string.

    Args:
        date: The date to format.
        fmt: The strftime format string.

    Returns:
        Formatted date string, or empty string if date is None.

    Example:
        >>> format_date(datetime(2024, 1, 15))
        '15/01/2024'
    """
    if date is None:
        return ''
    return date.strftime(fmt)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length, adding ellipsis if needed.

    Args:
        text: The text to truncate.
        max_length: Maximum number of characters.

    Returns:
        Truncated text string.

    Example:
        >>> truncate_text('Hello World', 5)
        'Hello...'
    """
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'


def get_status_badge_class(status: str) -> str:
    """Return a CSS badge class for a given status string.

    Args:
        status: The status value.

    Returns:
        A CSS class string for styling.
    """
    status_classes = {
        'planning': 'badge-secondary',
        'in_progress': 'badge-primary',
        'completed': 'badge-success',
        'on_hold': 'badge-warning',
        'cancelled': 'badge-danger',
        'todo': 'badge-secondary',
        'done': 'badge-success',
    }
    return status_classes.get(status, 'badge-secondary')
