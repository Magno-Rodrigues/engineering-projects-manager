"""Admin routes for user management."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _parse_date(value: str):
    """Parse a date string in YYYY-MM-DD format, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
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
    if success:
        flash('Usuário excluído com sucesso.', 'success')
    else:
        flash(error, 'error')
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
