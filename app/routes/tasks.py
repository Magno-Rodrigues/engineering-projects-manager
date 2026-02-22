"""Task routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.task import Task
from app.models.project import Project

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@tasks_bp.route('/project/<int:project_id>')
@login_required
def index(project_id: int):
    """List all tasks for a project."""
    tasks = Task.query.filter_by(project_id=project_id).all()
    return render_template('tasks/index.html', tasks=tasks, project_id=project_id)


@tasks_bp.route('/project/<int:project_id>/new', methods=['GET', 'POST'])
@login_required
def create(project_id: int):
    """Create a new task for a project."""
    if request.method == 'POST':
        task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            priority=request.form.get('priority', 'medium'),
            project_id=project_id,
            assignee_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('tasks.index', project_id=project_id))
    return render_template('tasks/create.html', project_id=project_id)


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id: int):
    """Edit an existing task."""
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if project.owner_id != current_user.id and task.assignee_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        task.title = request.form.get('title', task.title)
        task.description = request.form.get('description', task.description)
        task.status = request.form.get('status', task.status)
        task.priority = request.form.get('priority', task.priority)
        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('tasks.index', project_id=task.project_id))
    return render_template('tasks/edit.html', task=task)


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id: int):
    """Delete a task."""
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if project.owner_id != current_user.id:
        abort(403)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('tasks.index', project_id=project_id))
