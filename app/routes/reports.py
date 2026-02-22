"""Report routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.services.project_service import ProjectService

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/project/<int:project_id>')
@login_required
def index(project_id: int):
    """List all reports for a project."""
    reports = ReportService.get_project_reports(project_id)
    return render_template('reports/index.html', reports=reports, project_id=project_id)


@reports_bp.route('/project/<int:project_id>/new', methods=['GET', 'POST'])
@login_required
def create(project_id: int):
    """Create a new report for a project."""
    if request.method == 'POST':
        report, error = ReportService.create_report(
            title=request.form.get('title'),
            content=request.form.get('content'),
            report_type=request.form.get('report_type', 'progress'),
            project_id=project_id,
            author_id=current_user.id,
        )
        if report:
            flash('Report created successfully.', 'success')
            return redirect(url_for('reports.index', project_id=project_id))
        flash(error, 'error')
    return render_template('reports/create.html', project_id=project_id)


@reports_bp.route('/<int:report_id>')
@login_required
def detail(report_id: int):
    """Show report details."""
    report = ReportService.get_report(report_id)
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('projects.index'))
    project = ProjectService.get_project(report.project_id)
    if not project or project.owner_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    return render_template('reports/detail.html', report=report)
