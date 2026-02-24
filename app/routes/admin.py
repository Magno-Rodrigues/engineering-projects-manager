"""Admin routes for user management."""
<<<<<<< HEAD
from datetime import datetime
=======
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
<<<<<<< HEAD

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _parse_date(value: str):
    """Parse a date string in YYYY-MM-DD format, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
=======
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
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
<<<<<<< HEAD
    """Admin dashboard with basic statistics."""
    from app.models.user import User
    from app.models.project import Project
    total_users = User.query.count()
    total_projects = Project.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_projects=total_projects,
        active_users=active_users,
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """List all users with optional search filters."""
    search_key = request.args.get('search_key', '').strip()
    search_name = request.args.get('search_name', '').strip()
    users = AdminService.list_all_users(search_key=search_key, search_name=search_name)
    return render_template(
        'admin/users_list.html',
        users=users,
        search_key=search_key,
        search_name=search_name,
    )


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def users_create():
    """Create a new user."""
    if request.method == 'POST':
        data = {
            'username': request.form.get('username', ''),
            'email': request.form.get('email', ''),
            'password': request.form.get('password', ''),
            'full_name': request.form.get('full_name', ''),
            'role': request.form.get('role', 'engineer'),
            'phone': request.form.get('phone', ''),
            'job_title': request.form.get('job_title', ''),
            'company': request.form.get('company', ''),
            'supervisor': request.form.get('supervisor', ''),
            'birth_date': _parse_date(request.form.get('birth_date', '')),
            'appointment_start_date': _parse_date(request.form.get('appointment_start_date', '')),
            'measurement_criterion': request.form.get('measurement_criterion', ''),
            'is_active': request.form.get('status', 'active') == 'active',
        }
        user, error = AdminService.create_user(data)
        if user:
            flash(f'Usuário {user.username} criado com sucesso.', 'success')
            return redirect(url_for('admin.users_list'))
        flash(error, 'error')
    return render_template('admin/users_form.html', user=None, action='create')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def users_edit(user_id: int):
    """Edit an existing user."""
    user = AdminService.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin.users_list'))
    if request.method == 'POST':
        data = {
            'username': request.form.get('username', ''),
            'email': request.form.get('email', ''),
            'password': request.form.get('password', ''),
            'full_name': request.form.get('full_name', ''),
            'role': request.form.get('role', 'engineer'),
            'phone': request.form.get('phone', ''),
            'job_title': request.form.get('job_title', ''),
            'company': request.form.get('company', ''),
            'supervisor': request.form.get('supervisor', ''),
            'birth_date': _parse_date(request.form.get('birth_date', '')),
            'appointment_start_date': _parse_date(request.form.get('appointment_start_date', '')),
            'measurement_criterion': request.form.get('measurement_criterion', ''),
            'is_active': request.form.get('status', 'active') == 'active',
        }
        updated, error = AdminService.update_user(user_id, data)
        if updated:
            flash(f'Usuário {updated.username} atualizado com sucesso.', 'success')
            return redirect(url_for('admin.users_list'))
        flash(error, 'error')
    return render_template('admin/users_form.html', user=user, action='edit')


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def users_delete(user_id: int):
    """Delete a single user."""
    if user_id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'error')
        return redirect(url_for('admin.users_list'))
    success, error = AdminService.delete_user(user_id)
=======
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
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
    if success:
        flash('Usuário excluído com sucesso.', 'success')
    else:
        flash(error, 'error')
<<<<<<< HEAD
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/bulk-delete', methods=['POST'])
@login_required
@admin_required
def users_bulk_delete():
    """Delete multiple users at once."""
    raw_ids = request.form.getlist('user_ids')
    user_ids = []
    for raw in raw_ids:
        try:
            uid = int(raw)
            if uid != current_user.id:
                user_ids.append(uid)
        except (ValueError, TypeError):
            pass
    if not user_ids:
        flash('Nenhum usuário selecionado para exclusão.', 'warning')
        return redirect(url_for('admin.users_list'))
    deleted, _ = AdminService.delete_multiple_users(user_ids)
    flash(f'{deleted} usuário(s) excluído(s) com sucesso.', 'success')
    return redirect(url_for('admin.users_list'))
=======
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
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
