"""Admin routes for user management."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.services.permission_service import PermissionService
from app.constants import (
    SUPERVISION_TYPES, COMPANIES, STATES,
    MEASUREMENT_CRITERIA, USER_STATUS, USER_ROLES,
    VALID_MODULES, MODULE_FUNCTIONS, MODULES_METADATA,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DEFAULT_PERMISSIONS = {
    'can_edit_projects': False,
    'can_edit_tasks': False,
    'can_view_reports': False,
    'can_manage_users': False,
    'can_view_apontamentos': False,
    'can_create_apontamentos': False,
    'can_edit_apontamentos': False,
    'can_delete_apontamentos': False,
    'can_manage_cycles': False,
}


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics and recent data."""
    from app.models.user import User
    from app.models.project import Project
    from app.models.time_entry import TimeEntry
    from datetime import datetime, timezone, timedelta

    total_users = User.query.count()
    total_projects = Project.query.count()
    total_time_entries = TimeEntry.query.count()

    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    active_users_month = User.query.filter(
        User.last_login.isnot(None),
        User.last_login >= one_month_ago,
    ).count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_projects = (
        Project.query
        .options(joinedload(Project.owner))
        .order_by(Project.created_at.desc())
        .limit(5).all()
    )
    recent_time_entries = (
        TimeEntry.query
        .options(joinedload(TimeEntry.project))
        .order_by(TimeEntry.created_at.desc())
        .limit(5).all()
    )

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_projects=total_projects,
        total_time_entries=total_time_entries,
        active_users_month=active_users_month,
        recent_users=recent_users,
        recent_projects=recent_projects,
        recent_time_entries=recent_time_entries,
    )


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
            # Initialize function permissions for admin users (all non-admin modules)
            if user.role == 'admin':
                for module in VALID_MODULES:
                    if module != 'admin':
                        PermissionService.set_module_function_permissions(
                            user.id, module, MODULE_FUNCTIONS[module], granted_by_id=current_user.id
                        )
            # Send welcome email to the new user and notification email to the admin
            from app.services.email_service import (
                generate_reset_token,
                send_user_registration_email,
                send_admin_registration_notification,
            )
            token = generate_reset_token(user)
            reset_link = url_for('auth.reset_password', token=token.token, _external=True)
            send_user_registration_email(user, reset_link)
            send_admin_registration_notification(current_user, user)
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
        password_changed = bool(request.form.get('password', '').strip())
        updated, error = AdminService.update_user(user_id, request.form.to_dict(), admin_id=current_user.id)
        if updated:
            if password_changed:
                from app.services.email_service import generate_reset_token, send_password_reset_email
                token = generate_reset_token(updated)
                reset_link = url_for('auth.reset_password', token=token.token, _external=True)
                send_password_reset_email(updated, reset_link)
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
        for module_name in VALID_MODULES:
            granted = MODULE_FUNCTIONS[module_name] if module_name in request.form else []
            PermissionService.set_module_function_permissions(
                user_id=user_id,
                module_name=module_name,
                granted_functions=granted,
                granted_by_id=current_user.id,
            )
        flash('Permissões atualizadas com sucesso.', 'success')
        return redirect(url_for('admin.usuarios_index'))

    def user_has_module_access(uid, module_name):
        return PermissionService.has_module_access_via_functions(uid, module_name)

    return render_template(
        'admin/usuarios/permissoes.html',
        user=user,
        VALID_MODULES=VALID_MODULES,
        MODULES_METADATA=MODULES_METADATA,
        user_has_module_access=user_has_module_access,
    )
