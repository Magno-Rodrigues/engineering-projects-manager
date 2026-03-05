"""PMBOK HTML routes for Charter, Stakeholders, and Communication Plan."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.integration_service import ProjectIntegrationService
from app.services.stakeholder_service import StakeholderService
from app.services.communication_plan_service import CommunicationPlanService
from app.services.project_service import ProjectService
from app.models.communication_plan import FREQUENCIES, COMMUNICATION_METHODS, DISTRIBUTION_METHODS
from app.models.stakeholder import INTEREST_LEVELS, INFLUENCE_LEVELS, STAKEHOLDER_CATEGORIES
from app.utils.parse_helpers import parse_date

pmbok_bp = Blueprint('pmbok', __name__, url_prefix='/projects')


def _get_project_or_abort(project_id: int):
    """Return project if current user is admin or owner, else flash error and return None."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Projeto não encontrado.', 'error')
        return None
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Acesso negado.', 'error')
        return None
    return project


# ---------------------------------------------------------------------------
# Charter (TAP) HTML routes
# ---------------------------------------------------------------------------

@pmbok_bp.route('/<int:project_id>/charter', methods=['GET', 'POST'])
@login_required
def charter(project_id: int):
    """View or create the Project Charter (TAP)."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    charter_obj = ProjectIntegrationService.get_charter(project_id)

    if request.method == 'POST':
        charter_obj, error = ProjectIntegrationService.create_charter(
            project_id=project_id,
            created_by=current_user.id,
            business_case=request.form.get('business_case'),
            project_purpose=request.form.get('project_purpose'),
            success_criteria=request.form.get('success_criteria'),
            high_level_requirements=request.form.get('high_level_requirements'),
            high_level_risks=request.form.get('high_level_risks'),
            assumptions=request.form.get('assumptions'),
            constraints=request.form.get('constraints'),
            approved_budget=request.form.get('approved_budget') or None,
            scheduled_start_date=parse_date(request.form.get('scheduled_start_date')),
            scheduled_end_date=parse_date(request.form.get('scheduled_end_date')),
        )
        if charter_obj:
            flash('TAP criado com sucesso.', 'success')
            return redirect(url_for('pmbok.charter', project_id=project_id))
        flash(error, 'error')

    return render_template(
        'projects/charter.html',
        project=project,
        charter=charter_obj,
    )


@pmbok_bp.route('/<int:project_id>/charter/<int:charter_id>/approve', methods=['POST'])
@login_required
def approve_charter(project_id: int, charter_id: int):
    """Approve or reject a Project Charter."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    approved = request.form.get('action') == 'approve'
    _, error = ProjectIntegrationService.approve_charter(
        charter_id=charter_id,
        authorized_by=current_user.id,
        approved=approved,
        approval_date=parse_date(request.form.get('approval_date')),
    )
    if error:
        flash(error, 'error')
    else:
        flash('TAP aprovado.' if approved else 'TAP rejeitado.', 'success')
    return redirect(url_for('pmbok.charter', project_id=project_id))


# ---------------------------------------------------------------------------
# Stakeholder HTML routes
# ---------------------------------------------------------------------------

@pmbok_bp.route('/<int:project_id>/stakeholders', methods=['GET', 'POST'])
@login_required
def stakeholders(project_id: int):
    """List or add stakeholders for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        stakeholder, error = StakeholderService.create_stakeholder(
            project_id=project_id,
            name=request.form.get('name', '').strip(),
            role=request.form.get('role') or None,
            organization=request.form.get('organization') or None,
            email=request.form.get('email') or None,
            phone=request.form.get('phone') or None,
            interest_level=request.form.get('interest_level', 'medium'),
            influence_level=request.form.get('influence_level', 'medium'),
            category=request.form.get('category', 'other'),
            engagement_strategy=request.form.get('engagement_strategy') or None,
            communication_preference=request.form.get('communication_preference') or None,
            notes=request.form.get('notes') or None,
        )
        if stakeholder:
            flash('Stakeholder adicionado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('pmbok.stakeholders', project_id=project_id))

    stakeholder_list = StakeholderService.get_project_stakeholders(project_id)
    return render_template(
        'projects/stakeholders.html',
        project=project,
        stakeholders=stakeholder_list,
        interest_levels=INTEREST_LEVELS,
        influence_levels=INFLUENCE_LEVELS,
        categories=STAKEHOLDER_CATEGORIES,
    )


@pmbok_bp.route('/<int:project_id>/stakeholders/<int:stakeholder_id>/delete', methods=['POST'])
@login_required
def delete_stakeholder(project_id: int, stakeholder_id: int):
    """Remove a stakeholder from a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = StakeholderService.delete_stakeholder(stakeholder_id)
    if success:
        flash('Stakeholder removido.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('pmbok.stakeholders', project_id=project_id))


# ---------------------------------------------------------------------------
# Communication Plan HTML routes
# ---------------------------------------------------------------------------

@pmbok_bp.route('/<int:project_id>/communication-plan', methods=['GET', 'POST'])
@login_required
def communication_plan(project_id: int):
    """View or create the Communication Plan for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        plan, error = CommunicationPlanService.create_communication_plan(
            project_id=project_id,
            created_by=current_user.id,
            information=request.form.get('information', '').strip(),
            frequency=request.form.get('frequency', 'weekly'),
            responsible=request.form.get('responsible') or None,
            target_audience=request.form.get('target_audience') or None,
            communication_method=request.form.get('communication_method', 'email'),
            distribution_method=request.form.get('distribution_method', 'direct'),
            notes=request.form.get('notes') or None,
        )
        if plan:
            flash('Entrada adicionada ao plano de comunicação.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('pmbok.communication_plan', project_id=project_id))

    plans = CommunicationPlanService.get_project_communication_plans(project_id)
    return render_template(
        'projects/communication_plan.html',
        project=project,
        plans=plans,
        frequencies=FREQUENCIES,
        communication_methods=COMMUNICATION_METHODS,
        distribution_methods=DISTRIBUTION_METHODS,
    )


@pmbok_bp.route('/<int:project_id>/communication-plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_communication_plan(project_id: int, plan_id: int):
    """Remove an entry from the communication plan."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = CommunicationPlanService.delete_communication_plan(plan_id)
    if success:
        flash('Entrada removida do plano de comunicação.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('pmbok.communication_plan', project_id=project_id))
