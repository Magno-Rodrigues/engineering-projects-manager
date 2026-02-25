"""Admin routes for user listing and function-permission management."""
from typing import Dict
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.services.permission_service import PermissionService
from app.constants import VALID_MODULES, MODULE_FUNCTIONS, MODULE_DISPLAY_NAMES, FUNCTION_DISPLAY_NAMES

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')


@admin_users_bp.route('/')
@login_required
@admin_required
def list_users():
    """List all users with links to edit permissions (GET /admin/users)."""
    users = AdminService.list_users()
    return render_template(
        'admin/users/list.html',
        users=users,
        modules=VALID_MODULES,
        module_display_names=MODULE_DISPLAY_NAMES,
    )


@admin_users_bp.route('/<int:user_id>/edit')
@login_required
@admin_required
def edit_user(user_id: int):
    """Show the permission-editing page for a user (GET /admin/users/<id>/edit)."""
    user = AdminService.get_user(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_users.list_users'))
    return redirect(url_for('admin_users.user_permissions', user_id=user_id))


@admin_users_bp.route('/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def user_permissions(user_id: int):
    """View or update function permissions for a user.

    GET  /admin/users/<id>/permissions – show permission form
    POST /admin/users/<id>/permissions – save permissions
    """
    user = AdminService.get_user(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_users.list_users'))

    if request.method == 'POST':
        for module_name in VALID_MODULES:
            granted_functions = [
                fn for fn in MODULE_FUNCTIONS.get(module_name, [])
                if f'{module_name}__{fn}' in request.form
            ]
            PermissionService.set_module_function_permissions(
                user_id=user_id,
                module_name=module_name,
                granted_functions=granted_functions,
                granted_by_id=current_user.id,
            )
        flash('Permissões atualizadas com sucesso.', 'success')
        return redirect(url_for('admin_users.list_users'))

    # Build a dict: {module_name: {function_name: has_permission}}
    all_perms = PermissionService.get_user_function_permissions(user_id)
    perm_map: Dict[str, Dict[str, bool]] = {}
    for p in all_perms:
        perm_map.setdefault(p.module_name, {})[p.function_name] = p.has_permission

    return render_template(
        'admin/users/edit.html',
        user=user,
        modules=VALID_MODULES,
        module_functions=MODULE_FUNCTIONS,
        module_display_names=MODULE_DISPLAY_NAMES,
        function_display_names=FUNCTION_DISPLAY_NAMES,
        perm_map=perm_map,
    )
