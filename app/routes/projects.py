"""Project routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.project_service import ProjectService

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
@login_required
def index():
    """List all projects for the current user."""
    projects = ProjectService.get_user_projects(current_user.id)
    return render_template('projects/index.html', projects=projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        project, error = ProjectService.create_project(
            name=name,
            description=description,
            owner_id=current_user.id
        )
        if project:
            flash('Project created successfully.', 'success')
            return redirect(url_for('projects.detail', project_id=project.id))
        flash(error, 'error')
    return render_template('projects/create.html')


@projects_bp.route('/<int:project_id>')
@login_required
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
        }
        updated, error = ProjectService.update_project(project_id, data)
        if updated:
            flash('Project updated successfully.', 'success')
            return redirect(url_for('projects.detail', project_id=project_id))
        flash(error, 'error')
    return render_template('projects/edit.html', project=project)


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id: int):
    """Delete a project."""
    project = ProjectService.get_project(project_id)
    if project and project.owner_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    success, error = ProjectService.delete_project(project_id)
    if success:
        flash('Project deleted successfully.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('projects.index'))
