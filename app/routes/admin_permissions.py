"""Admin routes for module permission management."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.services.permission_service import PermissionService

admin_permissions_bp = Blueprint('admin_permissions', __name__, url_prefix='/admin')


@admin_permissions_bp.route('/permissoes')
@login_required
@admin_required
def permissoes_index():
    """List all users with their module permissions."""
    from app.models.user import User
    users = User.query.order_by(User.full_name).all()
    modules = PermissionService.get_available_modules()
    return render_template(
        'admin/permissoes/index.html',
        users=users,
        modules=modules,
    )


@admin_permissions_bp.route('/permissoes/usuario/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def permissoes_usuario(user_id: int):
    """View and update module permissions for a specific user."""
    user = AdminService.get_user(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_permissions.permissoes_index'))

    modules = PermissionService.get_available_modules()

    if request.method == 'POST':
        for module in modules:
            mn = module.module_name
            can_create = f'{mn}_create' in request.form
            can_read = f'{mn}_read' in request.form
            can_update = f'{mn}_update' in request.form
            can_delete = f'{mn}_delete' in request.form
            has_any = any([can_create, can_read, can_update, can_delete])
            if has_any:
                PermissionService.grant_module_permission(
                    user_id=user_id,
                    module_name=mn,
                    can_create=can_create,
                    can_read=can_read,
                    can_update=can_update,
                    can_delete=can_delete,
                    granted_by_id=current_user.id,
                )
            else:
                PermissionService.revoke_module_permission(user_id, mn)
        flash('Permissões de módulo atualizadas com sucesso.', 'success')
        return redirect(url_for('admin_permissions.permissoes_index'))

    user_perms = {p.module_name: p for p in PermissionService.get_user_modules(user_id)}
    return render_template(
        'admin/permissoes/usuario.html',
        user=user,
        modules=modules,
        user_perms=user_perms,
    )
