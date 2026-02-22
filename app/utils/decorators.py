"""Custom decorators for the application."""
from functools import wraps
from typing import Callable
from flask import abort
from flask_login import current_user


def role_required(role: str) -> Callable:
    """Decorator to restrict access to users with a specific role.

    Args:
        role: The required role string (e.g., 'admin', 'engineer').

    Example:
        @role_required('admin')
        def admin_view():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to restrict access to admin users only.

    Example:
        @admin_required
        def admin_only_view():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
