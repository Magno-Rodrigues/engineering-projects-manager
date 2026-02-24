"""Permission decorators for module-based access control."""
from functools import wraps
from typing import Callable
from flask import abort
from flask_login import current_user


def module_required(module_name: str) -> Callable:
    """Decorator to require any access to a module.

    Admins bypass this check entirely.

    Args:
        module_name: The module identifier (e.g., 'projects').

    Example:
        @module_required('projects')
        def projects_view():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            from app.services.permission_service import PermissionService
            if not PermissionService.has_module_access(current_user.id, module_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def action_required(module_name: str, action: str) -> Callable:
    """Decorator to require a specific CRUD action on a module.

    Admins bypass this check entirely.

    Args:
        module_name: The module identifier (e.g., 'projects').
        action: One of 'create', 'read', 'update', 'delete'.

    Example:
        @action_required('projects', 'create')
        def create_project():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            from app.services.permission_service import PermissionService
            if not PermissionService.can_perform_action(current_user.id, module_name, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_or_owner_required(get_object_fn: Callable, id_kwarg: str = 'project_id') -> Callable:
    """Decorator to restrict access to admins or resource owners.

    Admins have full access. Regular users can only access resources they own.

    Args:
        get_object_fn: Callable that accepts an ID and returns the object.
                       The object must have an owner_id attribute.
        id_kwarg: Name of the route keyword argument containing the object ID.

    Example:
        @admin_or_owner_required(ProjectService.get_project)
        def detail(project_id: int):
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            obj_id = kwargs.get(id_kwarg)
            obj = get_object_fn(obj_id)
            if not obj:
                abort(404)
            if obj.owner_id != current_user.id:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
