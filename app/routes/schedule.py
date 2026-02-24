"""Schedule management routes (PMBOK - Prazo)."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.services.schedule_service import ScheduleService
from app.services.scope_service import ScopeService

schedule_bp = Blueprint('schedule', __name__, url_prefix='/projects/<int:project_id>/schedule')


def _get_project_or_abort(project_id):
    """Return project if owned by current user, else redirect."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return None, redirect(url_for('projects.index'))
    if project.owner_id != current_user.id:
        flash('Access denied.', 'error')
        return None, redirect(url_for('projects.index'))
    return project, None


def _parse_date(date_str):
    """Parse date string YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# -------------------------
# Activities
# -------------------------

@schedule_bp.route('/')
@login_required
def index(project_id: int):
    """Show schedule overview."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    activities = ScheduleService.get_activities(project_id)
    milestones = ScheduleService.get_milestones(project_id)
    variance = ScheduleService.calculate_schedule_variance(project_id)
    return render_template(
        'schedule/index.html',
        project=project,
        activities=activities,
        milestones=milestones,
        variance=variance,
    )


@schedule_bp.route('/activities/new', methods=['GET', 'POST'])
@login_required
def create_activity(project_id: int):
    """Create a new activity."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        dur = request.form.get('estimated_duration')
        try:
            dur = int(dur) if dur else None
        except (ValueError, TypeError):
            dur = None
        activity, error = ScheduleService.create_activity(
            project_id=project_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
            estimated_duration=dur,
            created_by=current_user.id,
        )
        if activity:
            flash('Activity created successfully.', 'success')
            return redirect(url_for('schedule.index', project_id=project_id))
        flash(error, 'error')
    wbs_items = ScopeService.get_wbs_items(project_id)
    return render_template('schedule/activity_form.html', project=project, activity=None, wbs_items=wbs_items)


@schedule_bp.route('/activities/<int:activity_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(project_id: int, activity_id: int):
    """Edit an activity."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    activity = ScheduleService.get_activity(activity_id)
    if not activity or activity.project_id != project_id:
        flash('Activity not found.', 'error')
        return redirect(url_for('schedule.index', project_id=project_id))
    if request.method == 'POST':
        dur = request.form.get('estimated_duration')
        try:
            dur = int(dur) if dur else None
        except (ValueError, TypeError):
            dur = None
        updated, error = ScheduleService.update_activity(
            activity_id,
            {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'start_date': _parse_date(request.form.get('start_date')),
                'end_date': _parse_date(request.form.get('end_date')),
                'estimated_duration': dur,
                'progress': request.form.get('progress', 0),
                'status': request.form.get('status'),
            },
            updated_by=current_user.id,
        )
        if updated:
            flash('Activity updated successfully.', 'success')
            return redirect(url_for('schedule.index', project_id=project_id))
        flash(error, 'error')
    wbs_items = ScopeService.get_wbs_items(project_id)
    return render_template('schedule/activity_form.html', project=project, activity=activity, wbs_items=wbs_items)


@schedule_bp.route('/activities/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(project_id: int, activity_id: int):
    """Delete an activity."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    ScheduleService.delete_activity(activity_id)
    flash('Activity deleted.', 'success')
    return redirect(url_for('schedule.index', project_id=project_id))


# -------------------------
# Milestones
# -------------------------

@schedule_bp.route('/milestones/new', methods=['GET', 'POST'])
@login_required
def create_milestone(project_id: int):
    """Create a new milestone."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        milestone, error = ScheduleService.create_milestone(
            project_id=project_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            target_date=_parse_date(request.form.get('target_date')),
            created_by=current_user.id,
        )
        if milestone:
            flash('Milestone created successfully.', 'success')
            return redirect(url_for('schedule.index', project_id=project_id))
        flash(error, 'error')
    return render_template('schedule/milestone_form.html', project=project, milestone=None)


@schedule_bp.route('/milestones/<int:milestone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_milestone(project_id: int, milestone_id: int):
    """Edit a milestone."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    milestone = ScheduleService.get_milestone(milestone_id)
    if not milestone or milestone.project_id != project_id:
        flash('Milestone not found.', 'error')
        return redirect(url_for('schedule.index', project_id=project_id))
    if request.method == 'POST':
        updated, error = ScheduleService.update_milestone(
            milestone_id,
            {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'target_date': _parse_date(request.form.get('target_date')),
                'actual_date': _parse_date(request.form.get('actual_date')),
                'status': request.form.get('status'),
            },
            updated_by=current_user.id,
        )
        if updated:
            flash('Milestone updated successfully.', 'success')
            return redirect(url_for('schedule.index', project_id=project_id))
        flash(error, 'error')
    return render_template('schedule/milestone_form.html', project=project, milestone=milestone)


@schedule_bp.route('/milestones/<int:milestone_id>/delete', methods=['POST'])
@login_required
def delete_milestone(project_id: int, milestone_id: int):
    """Delete a milestone."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    ScheduleService.delete_milestone(milestone_id)
    flash('Milestone deleted.', 'success')
    return redirect(url_for('schedule.index', project_id=project_id))
