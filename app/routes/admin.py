"""Admin routes for user management."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.constants import (
    SUPERVISION_TYPES, COMPANIES, STATES,
    MEASUREMENT_CRITERIA, USER_STATUS, USER_ROLES,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DEFAULT_PERMISSIONS = {
    'can_edit_projects': False,
    'can_edit_tasks': False,
    'can_view_reports': False,
    'can_manage_users': False,
}


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    from app.models.user import User
    total_users = User.query.count()
    return render_template('admin/dashboard.html', total_users=total_users)


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios_index():
    """List users with optional filters."""
    key_filter = request.args.get('key', '').strip()
    name_filter = request.args.get('name', '').strip()
    users = AdminService.list_users(key_filter=key_filter, name_filter=name_filter)
    return render_template(
        'admin/usuarios/index.html',
        users=users,
        key_filter=key_filter,
        name_filter=name_filter,
    )


@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def usuarios_novo():
    """Create a new user."""
    if request.method == 'POST':
        user, error = AdminService.create_user(request.form.to_dict(), admin_id=current_user.id)
        if user:
            flash(f'Usuário {user.username} cadastrado com sucesso.', 'success')
            return redirect(url_for('admin.usuarios_index'))
        flash(error, 'error')
    return render_template(
        'admin/usuarios/form.html',
        user=None,
        supervision_types=SUPERVISION_TYPES,
        companies=COMPANIES,
        states=STATES,
        measurement_criteria=MEASUREMENT_CRITERIA,
        user_status=USER_STATUS,
        user_roles=USER_ROLES,
    )


@admin_bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def usuarios_editar(user_id: int):
    """Edit an existing user."""
    user = AdminService.get_user(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin.usuarios_index'))
    if request.method == 'POST':
        updated, error = AdminService.update_user(user_id, request.form.to_dict(), admin_id=current_user.id)
        if updated:
            flash('Usuário atualizado com sucesso.', 'success')
            return redirect(url_for('admin.usuarios_index'))
        flash(error, 'error')
    return render_template(
        'admin/usuarios/form.html',
        user=user,
        supervision_types=SUPERVISION_TYPES,
        companies=COMPANIES,
        states=STATES,
        measurement_criteria=MEASUREMENT_CRITERIA,
        user_status=USER_STATUS,
        user_roles=USER_ROLES,
    )


@admin_bp.route('/usuarios/<int:user_id>/deletar', methods=['POST'])
@login_required
@admin_required
def usuarios_deletar(user_id: int):
    """Delete a user."""
    success, error = AdminService.delete_user(user_id, admin_id=current_user.id)
    if success:
        flash('Usuário excluído com sucesso.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('admin.usuarios_index'))


@admin_bp.route('/usuarios/deletar-selecionados', methods=['POST'])
@login_required
@admin_required
def usuarios_deletar_selecionados():
    """Delete multiple selected users."""
    ids = request.form.getlist('selected_ids')
    deleted = 0
    for uid in ids:
        try:
            success, _ = AdminService.delete_user(int(uid), admin_id=current_user.id)
            if success:
                deleted += 1
        except (ValueError, TypeError):
            continue
    flash(f'{deleted} usuário(s) excluído(s) com sucesso.', 'success')
    return redirect(url_for('admin.usuarios_index'))


@admin_bp.route('/usuarios/<int:user_id>/permissoes', methods=['GET', 'POST'])
@login_required
@admin_required
def usuarios_permissoes(user_id: int):
    """Manage user permissions."""
    user = AdminService.get_user(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin.usuarios_index'))
    if request.method == 'POST':
        permissions = {
            'can_edit_projects': 'can_edit_projects' in request.form,
            'can_edit_tasks': 'can_edit_tasks' in request.form,
            'can_view_reports': 'can_view_reports' in request.form,
            'can_manage_users': 'can_manage_users' in request.form,
        }
        updated, error = AdminService.update_permissions(user_id, permissions, admin_id=current_user.id)
        if updated:
            flash('Permissões atualizadas com sucesso.', 'success')
            return redirect(url_for('admin.usuarios_index'))
        flash(error, 'error')
    current_permissions = user.permissions or DEFAULT_PERMISSIONS.copy()
    return render_template(
        'admin/usuarios/permissoes.html',
        user=user,
        permissions=current_permissions,
    )
