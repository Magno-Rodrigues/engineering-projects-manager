"""Task routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.task import Task, PMBOK_KNOWLEDGE_AREAS, PMBOK_PROCESS_GROUPS
from app.models.project import Project
from app.models.wbs_item import WBSItem
from app.models.user import User

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@tasks_bp.route('/project/<int:project_id>')
@login_required
def index(project_id: int):
    """List all tasks for a project."""
    project = Project.query.get_or_404(project_id)
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    tasks = Task.query.filter_by(project_id=project_id).all()
    return render_template('tasks/index.html', tasks=tasks, project_id=project_id)


@tasks_bp.route('/project/<int:project_id>/new', methods=['GET', 'POST'])
@login_required
def create(project_id: int):
    """Create a new task for a project."""
    project = Project.query.get_or_404(project_id)
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        effort_str = request.form.get('estimated_effort')
        progress_str = request.form.get('progress', '0')
        assignee_id_str = request.form.get('assignee_id')
        task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            priority=request.form.get('priority', 'medium'),
            project_id=project_id,
            assignee_id=int(assignee_id_str) if assignee_id_str else current_user.id,
            pmbok_knowledge_area=request.form.get('pmbok_knowledge_area') or None,
            pmbok_process_group=request.form.get('pmbok_process_group') or None,
            wbs_item_id=request.form.get('wbs_item_id') or None,
            start_date=_parse_date(request.form.get('start_date')),
            due_date=_parse_date(request.form.get('due_date')),
            estimated_effort=effort_str if effort_str else None,
            progress=int(progress_str) if progress_str else 0,
            dependencies=request.form.get('dependencies') or None,
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('tasks.index', project_id=project_id))
    wbs_items = WBSItem.query.filter_by(project_id=project_id).all()
    users = User.query.filter_by(is_active=True).all()
    return render_template(
        'tasks/create.html',
        project_id=project_id,
        wbs_items=wbs_items,
        users=users,
        pmbok_knowledge_areas=PMBOK_KNOWLEDGE_AREAS,
        pmbok_process_groups=PMBOK_PROCESS_GROUPS,
    )


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id: int):
    """Edit an existing task."""
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if not (current_user.role == 'admin' or project.owner_id == current_user.id or task.assignee_id == current_user.id):
        abort(403)
    if request.method == 'POST':
        effort_str = request.form.get('estimated_effort')
        progress_str = request.form.get('progress', '0')
        assignee_id_str = request.form.get('assignee_id')
        task.title = request.form.get('title', task.title)
        task.description = request.form.get('description', task.description)
        task.status = request.form.get('status', task.status)
        task.priority = request.form.get('priority', task.priority)
        task.assignee_id = int(assignee_id_str) if assignee_id_str else None
        task.pmbok_knowledge_area = request.form.get('pmbok_knowledge_area') or None
        task.pmbok_process_group = request.form.get('pmbok_process_group') or None
        task.wbs_item_id = request.form.get('wbs_item_id') or None
        task.start_date = _parse_date(request.form.get('start_date'))
        task.due_date = _parse_date(request.form.get('due_date'))
        task.estimated_effort = effort_str if effort_str else None
        task.progress = int(progress_str) if progress_str else 0
        task.dependencies = request.form.get('dependencies') or None
        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('tasks.index', project_id=task.project_id))
    wbs_items = WBSItem.query.filter_by(project_id=task.project_id).all()
    users = User.query.filter_by(is_active=True).all()
    return render_template(
        'tasks/edit.html',
        task=task,
        wbs_items=wbs_items,
        users=users,
        pmbok_knowledge_areas=PMBOK_KNOWLEDGE_AREAS,
        pmbok_process_groups=PMBOK_PROCESS_GROUPS,
    )


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id: int):
    """Delete a task."""
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        abort(403)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('tasks.index', project_id=project_id))
