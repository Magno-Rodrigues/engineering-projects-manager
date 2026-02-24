"""Cost management routes (PMBOK - Custo)."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.services.cost_service import CostService
from app.services.scope_service import ScopeService
from app.services.schedule_service import ScheduleService

cost_bp = Blueprint('cost', __name__, url_prefix='/projects/<int:project_id>/cost')


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
# Budget Lines
# -------------------------

@cost_bp.route('/')
@login_required
def index(project_id: int):
    """Show cost overview."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    budget_lines = CostService.get_budget_lines(project_id)
    cost_variances = CostService.get_cost_variances(project_id)
    summary = CostService.get_cost_variance_summary(project_id)
    cost_baselines = CostService.get_cost_baselines(project_id)
    return render_template(
        'cost/index.html',
        project=project,
        budget_lines=budget_lines,
        cost_variances=cost_variances,
        summary=summary,
        cost_baselines=cost_baselines,
    )


@cost_bp.route('/budget-lines/new', methods=['GET', 'POST'])
@login_required
def create_budget_line(project_id: int):
    """Create a new budget line."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        line, error = CostService.create_budget_line(
            project_id=project_id,
            title=request.form.get('title'),
            planned_value=request.form.get('planned_value'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            actual_cost=request.form.get('actual_cost'),
            reference_date=_parse_date(request.form.get('reference_date')),
            created_by=current_user.id,
        )
        if line:
            flash('Budget line created successfully.', 'success')
            return redirect(url_for('cost.index', project_id=project_id))
        flash(error, 'error')
    wbs_items = ScopeService.get_wbs_items(project_id)
    activities = ScheduleService.get_activities(project_id)
    return render_template(
        'cost/budget_line_form.html',
        project=project,
        budget_line=None,
        wbs_items=wbs_items,
        activities=activities,
    )


@cost_bp.route('/budget-lines/<int:line_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget_line(project_id: int, line_id: int):
    """Edit a budget line."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    line = CostService.get_budget_line(line_id)
    if not line or line.project_id != project_id:
        flash('Budget line not found.', 'error')
        return redirect(url_for('cost.index', project_id=project_id))
    if request.method == 'POST':
        updated, error = CostService.update_budget_line(
            line_id,
            {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'planned_value': request.form.get('planned_value'),
                'actual_cost': request.form.get('actual_cost'),
                'reference_date': _parse_date(request.form.get('reference_date')),
                'status': request.form.get('status'),
            },
            updated_by=current_user.id,
        )
        if updated:
            flash('Budget line updated successfully.', 'success')
            return redirect(url_for('cost.index', project_id=project_id))
        flash(error, 'error')
    wbs_items = ScopeService.get_wbs_items(project_id)
    activities = ScheduleService.get_activities(project_id)
    return render_template(
        'cost/budget_line_form.html',
        project=project,
        budget_line=line,
        wbs_items=wbs_items,
        activities=activities,
    )


@cost_bp.route('/budget-lines/<int:line_id>/delete', methods=['POST'])
@login_required
def delete_budget_line(project_id: int, line_id: int):
    """Delete a budget line."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    CostService.delete_budget_line(line_id)
    flash('Budget line deleted.', 'success')
    return redirect(url_for('cost.index', project_id=project_id))


# -------------------------
# Cost Variance (EV Metrics)
# -------------------------

@cost_bp.route('/variance/new', methods=['GET', 'POST'])
@login_required
def create_cost_variance(project_id: int):
    """Create a cost variance record."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        cv, error = CostService.create_cost_variance(
            project_id=project_id,
            reference_date=_parse_date(request.form.get('reference_date')),
            planned_value=request.form.get('planned_value'),
            earned_value=request.form.get('earned_value'),
            actual_cost=request.form.get('actual_cost'),
            notes=request.form.get('notes'),
            created_by=current_user.id,
        )
        if cv:
            flash('Cost variance record created.', 'success')
            return redirect(url_for('cost.index', project_id=project_id))
        flash(error, 'error')
    return render_template('cost/cost_variance_form.html', project=project)


# -------------------------
# S-Curve (JSON for chart)
# -------------------------

@cost_bp.route('/s-curve')
@login_required
def s_curve(project_id: int):
    """Return S-curve data as JSON."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return jsonify({'error': 'Access denied'}), 403
    data = CostService.get_s_curve_data(project_id)
    return jsonify(data)


# -------------------------
# Cost Baselines
# -------------------------

@cost_bp.route('/baselines/new', methods=['GET', 'POST'])
@login_required
def create_cost_baseline(project_id: int):
    """Create a cost baseline."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        baseline, error = CostService.create_cost_baseline(
            project_id=project_id,
            name=request.form.get('name'),
            total_budget=request.form.get('total_budget'),
            description=request.form.get('description'),
            created_by=current_user.id,
        )
        if baseline:
            flash('Cost baseline created successfully.', 'success')
            return redirect(url_for('cost.index', project_id=project_id))
        flash(error, 'error')
    return render_template('cost/cost_baseline_form.html', project=project)
