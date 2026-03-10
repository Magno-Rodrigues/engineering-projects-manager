"""Project routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.utils.permission_decorators import module_required, action_required, admin_or_owner_required
from app.constants import PROJECT_STATUS, PROJECT_PRIORITY, PROJECT_CATEGORIES

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


def _parse_date(date_str):
    """Parse a date string into a date object.
    
    Args:
        date_str: Date string in format YYYY-MM-DD or None
        
    Returns:
        datetime.date object or None
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@projects_bp.route('/')
@login_required
@module_required('projects')
@action_required('projects', 'read')
def index():
    """List all projects for the current user with filtering and sorting."""
    from app.models.project import Project
    from app.models.task import Task
    from sqlalchemy import or_

    is_admin = current_user.role == 'admin'
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    client_filter = request.args.get('client', '').strip()
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')
    view_mode = request.args.get('view', 'card')

    projects = ProjectService.get_user_projects(current_user.id, include_all=is_admin)

    # Apply search / filters in Python (projects already scoped to user)
    if search:
        search_lower = search.lower()
        projects = [p for p in projects if search_lower in (p.name or '').lower()]
    if status_filter:
        projects = [p for p in projects if p.status == status_filter]
    if client_filter:
        client_lower = client_filter.lower()
        projects = [p for p in projects if p.client_name and client_lower in p.client_name.lower()]

    # Sorting
    reverse = sort_dir == 'desc'
    if sort_by == 'name':
        projects.sort(key=lambda p: (p.name or '').lower(), reverse=reverse)
    elif sort_by == 'status':
        projects.sort(key=lambda p: (p.status or ''), reverse=reverse)
    elif sort_by == 'budget':
        projects.sort(key=lambda p: float(p.budget or 0), reverse=reverse)
    else:
        projects.sort(key=lambda p: p.created_at or '', reverse=reverse)

    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    pending_tasks = Task.query.filter_by(status='pending').count()

    # Unique client names for filter dropdown
    all_projects = ProjectService.get_user_projects(current_user.id, include_all=is_admin)
    client_names = sorted({p.client_name for p in all_projects if p.client_name})

    return render_template(
        'projects/index.html',
        projects=projects,
        recent_projects=recent_projects,
        pending_tasks=pending_tasks,
        search=search,
        status_filter=status_filter,
        client_filter=client_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
        view_mode=view_mode,
        client_names=client_names,
        statuses=PROJECT_STATUS,
    )


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
@module_required('projects')
@action_required('projects', 'create')
def create():
    """Create a new project."""
    if request.method == 'POST':
        start_date = _parse_date(request.form.get('start_date'))
        end_date = _parse_date(request.form.get('end_date'))
        project, error = ProjectService.create_project(
            name=request.form.get('name'),
            description=request.form.get('description'),
            owner_id=current_user.id,
            status=request.form.get('status'),
            start_date=start_date,
            end_date=end_date,
            budget=request.form.get('budget'),
            actual_cost=request.form.get('actual_cost'),
            category=request.form.get('category'),
            priority=request.form.get('priority'),
            location=request.form.get('location'),
            client_name=request.form.get('client_name'),
            notes=request.form.get('notes'),
        )
        if project:
            flash('Project created successfully.', 'success')
            return redirect(url_for('projects.detail', project_id=project.id))
        flash(error, 'error')
    return render_template(
        'projects/create.html',
        statuses=PROJECT_STATUS,
        priorities=PROJECT_PRIORITY,
        categories=PROJECT_CATEGORIES,
    )


@projects_bp.route('/<int:project_id>')
@login_required
@module_required('projects')
@action_required('projects', 'read')
@admin_or_owner_required(ProjectService.get_project)
def detail(project_id: int):
    """Show project details."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    return render_template('projects/detail.html', project=project)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@module_required('projects')
@action_required('projects', 'update')
@admin_or_owner_required(ProjectService.get_project)
def edit(project_id: int):
    """Edit an existing project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'status': request.form.get('status'),
            'start_date': _parse_date(request.form.get('start_date')),
            'end_date': _parse_date(request.form.get('end_date')),
            'budget': request.form.get('budget'),
            'actual_cost': request.form.get('actual_cost'),
            'category': request.form.get('category'),
            'priority': request.form.get('priority'),
            'location': request.form.get('location'),
            'client_name': request.form.get('client_name'),
            'notes': request.form.get('notes'),
        }
        updated, error = ProjectService.update_project(project_id, data)
        if updated:
            flash('Project updated successfully.', 'success')
            return redirect(url_for('projects.detail', project_id=project_id))
        flash(error, 'error')
    return render_template(
        'projects/edit.html',
        project=project,
        statuses=PROJECT_STATUS,
        priorities=PROJECT_PRIORITY,
        categories=PROJECT_CATEGORIES,
    )


@projects_bp.route('/<int:project_id>/toggle-status', methods=['POST'])
@login_required
@module_required('projects')
@action_required('projects', 'update')
@admin_or_owner_required(ProjectService.get_project)
def toggle_status(project_id: int):
    """Toggle a project's status between 'planning' and 'blocked'."""
    project, error = ProjectService.toggle_project_status(project_id)
    if project:
        status_label = 'bloqueado' if project.status == 'blocked' else 'desbloqueado'
        flash(f'Projeto {status_label} com sucesso.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('projects.detail', project_id=project_id))


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@module_required('projects')
@action_required('projects', 'delete')
@admin_or_owner_required(ProjectService.get_project)
def delete(project_id: int):
    """Delete a project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    
    ProjectService.delete_project(project_id)
    flash('Project deleted successfully.', 'success')
    return redirect(url_for('projects.index'))