"""Project routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.utils.permission_decorators import module_required, action_required
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
    """List all projects for the current user."""
    projects = ProjectService.get_user_projects(current_user.id)
    return render_template('projects/index.html', projects=projects)


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
def detail(project_id: int):
    """Show project details."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if project.owner_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    return render_template('projects/detail.html', project=project)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@module_required('projects')
@action_required('projects', 'update')
def edit(project_id: int):
    """Edit an existing project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if project.owner_id != current_user.id:
        flash('Access denied.', 'error')
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


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@module_required('projects')
@action_required('projects', 'delete')
def delete(project_id: int):
    """Delete a project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if project.owner_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    
    ProjectService.delete_project(project_id)
    flash('Project deleted successfully.', 'success')
    return redirect(url_for('projects.index'))