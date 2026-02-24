"""Report routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.services.report_service import ReportService
from app.services.project_service import ProjectService
from app.models.report import REPORT_TYPES
from app.models.user import User

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _parse_decimal(value_str):
    """Parse a string to float or return None."""
    if not value_str:
        return None
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return None


@reports_bp.route('/project/<int:project_id>')
@login_required
def index(project_id: int):
    """List all reports for a project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    reports = ReportService.get_project_reports(project_id)
    return render_template('reports/index.html', reports=reports, project_id=project_id)


@reports_bp.route('/project/<int:project_id>/new', methods=['GET', 'POST'])
@login_required
def create(project_id: int):
    """Create a new report for a project."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects.index'))
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        report, error = ReportService.create_report(
            title=request.form.get('title'),
            content=request.form.get('content'),
            report_type=request.form.get('report_type', 'progress'),
            project_id=project_id,
            author_id=current_user.id,
            report_date=_parse_date(request.form.get('report_date')),
            period_start=_parse_date(request.form.get('period_start')),
            period_end=_parse_date(request.form.get('period_end')),
            executive_summary=request.form.get('executive_summary') or None,
            scope_complete_pct=_parse_decimal(request.form.get('scope_complete_pct')),
            schedule_variance=_parse_decimal(request.form.get('schedule_variance')),
            cost_variance=_parse_decimal(request.form.get('cost_variance')),
            risks_identified=request.form.get('risks_identified') or None,
            current_issues=request.form.get('current_issues') or None,
            completed_tasks_text=request.form.get('completed_tasks_text') or None,
            tasks_in_progress_text=request.form.get('tasks_in_progress_text') or None,
            next_activities=request.form.get('next_activities') or None,
            corrective_actions=request.form.get('corrective_actions') or None,
            attention_points=request.form.get('attention_points') or None,
            approved_by_id=request.form.get('approved_by_id') or None,
        )
        if report:
            flash('Report created successfully.', 'success')
            return redirect(url_for('reports.index', project_id=project_id))
        flash(error, 'error')
    users = User.query.filter_by(is_active=True).all()
    return render_template(
        'reports/create.html',
        project_id=project_id,
        users=users,
        report_types=REPORT_TYPES,
    )


@reports_bp.route('/<int:report_id>')
@login_required
def detail(report_id: int):
    """Show report details."""
    report = ReportService.get_report(report_id)
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('projects.index'))
    project = ProjectService.get_project(report.project_id)
    if not project or not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    return render_template('reports/detail.html', report=report)


@reports_bp.route('/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(report_id: int):
    """Edit an existing report."""
    report = ReportService.get_report(report_id)
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('projects.index'))
    project = ProjectService.get_project(report.project_id)
    if not project or not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        report.title = request.form.get('title', report.title)
        report.content = request.form.get('content', report.content)
        report.report_type = request.form.get('report_type', report.report_type)
        report.report_date = _parse_date(request.form.get('report_date'))
        report.period_start = _parse_date(request.form.get('period_start'))
        report.period_end = _parse_date(request.form.get('period_end'))
        report.executive_summary = request.form.get('executive_summary') or None
        report.scope_complete_pct = _parse_decimal(request.form.get('scope_complete_pct'))
        report.schedule_variance = _parse_decimal(request.form.get('schedule_variance'))
        report.cost_variance = _parse_decimal(request.form.get('cost_variance'))
        report.risks_identified = request.form.get('risks_identified') or None
        report.current_issues = request.form.get('current_issues') or None
        report.completed_tasks_text = request.form.get('completed_tasks_text') or None
        report.tasks_in_progress_text = request.form.get('tasks_in_progress_text') or None
        report.next_activities = request.form.get('next_activities') or None
        report.corrective_actions = request.form.get('corrective_actions') or None
        report.attention_points = request.form.get('attention_points') or None
        approved_by_id_str = request.form.get('approved_by_id')
        report.approved_by_id = int(approved_by_id_str) if approved_by_id_str else None
        db.session.commit()
        flash('Report updated successfully.', 'success')
        return redirect(url_for('reports.detail', report_id=report.id))
    users = User.query.filter_by(is_active=True).all()
    return render_template(
        'reports/edit.html',
        report=report,
        users=users,
        report_types=REPORT_TYPES,
    )


@reports_bp.route('/<int:report_id>/delete', methods=['POST'])
@login_required
def delete(report_id: int):
    """Delete a report."""
    report = ReportService.get_report(report_id)
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('projects.index'))
    project = ProjectService.get_project(report.project_id)
    if not project or not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    project_id = report.project_id
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted successfully.', 'success')
    return redirect(url_for('reports.index', project_id=project_id))
