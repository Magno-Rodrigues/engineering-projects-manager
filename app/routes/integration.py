"""Project Integration routes (PMBOK Integration Knowledge Area)."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.integration_service import ProjectIntegrationService
from app.utils.parse_helpers import parse_date as _parse_date

integration_bp = Blueprint('integration', __name__, url_prefix='/api/projects')


# ---------------------------------------------------------------------------
# Charter (TAP) endpoints
# ---------------------------------------------------------------------------

@integration_bp.route('/<int:project_id>/charter', methods=['GET'])
@login_required
def get_charter(project_id: int):
    """Return the most recent charter for a project."""
    charter = ProjectIntegrationService.get_charter(project_id)
    if not charter:
        return jsonify({'error': 'Charter not found'}), 404
    return jsonify({
        'id': charter.id,
        'project_id': charter.project_id,
        'created_by': charter.created_by,
        'authorized_by': charter.authorized_by,
        'business_case': charter.business_case,
        'project_purpose': charter.project_purpose,
        'success_criteria': charter.success_criteria,
        'high_level_requirements': charter.high_level_requirements,
        'high_level_risks': charter.high_level_risks,
        'assumptions': charter.assumptions,
        'constraints': charter.constraints,
        'approved_budget': str(charter.approved_budget) if charter.approved_budget is not None else None,
        'scheduled_start_date': charter.scheduled_start_date.isoformat() if charter.scheduled_start_date else None,
        'scheduled_end_date': charter.scheduled_end_date.isoformat() if charter.scheduled_end_date else None,
        'approval_date': charter.approval_date.isoformat() if charter.approval_date else None,
        'status': charter.status,
        'created_at': charter.created_at.isoformat(),
        'updated_at': charter.updated_at.isoformat(),
    })


@integration_bp.route('/<int:project_id>/charter', methods=['POST'])
@login_required
def create_charter(project_id: int):
    """Create a new Project Charter (TAP) for a project."""
    data = request.get_json(silent=True) or {}
    charter, error = ProjectIntegrationService.create_charter(
        project_id=project_id,
        created_by=current_user.id,
        business_case=data.get('business_case'),
        project_purpose=data.get('project_purpose'),
        success_criteria=data.get('success_criteria'),
        high_level_requirements=data.get('high_level_requirements'),
        high_level_risks=data.get('high_level_risks'),
        assumptions=data.get('assumptions'),
        constraints=data.get('constraints'),
        approved_budget=data.get('approved_budget'),
        scheduled_start_date=_parse_date(data.get('scheduled_start_date')),
        scheduled_end_date=_parse_date(data.get('scheduled_end_date')),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': charter.id, 'status': charter.status}), 201


@integration_bp.route('/<int:project_id>/charter/<int:charter_id>/approve', methods=['POST'])
@login_required
def approve_charter(project_id: int, charter_id: int):
    """Approve or reject a Project Charter."""
    data = request.get_json(silent=True) or {}
    approved = data.get('approved', True)
    charter, error = ProjectIntegrationService.approve_charter(
        charter_id=charter_id,
        authorized_by=current_user.id,
        approved=bool(approved),
        approval_date=_parse_date(data.get('approval_date')),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': charter.id, 'status': charter.status})


# ---------------------------------------------------------------------------
# Closure endpoints
# ---------------------------------------------------------------------------

@integration_bp.route('/<int:project_id>/closure', methods=['POST'])
@login_required
def create_closure(project_id: int):
    """Create a Project Closure document."""
    data = request.get_json(silent=True) or {}
    closure, error = ProjectIntegrationService.create_closure(
        project_id=project_id,
        created_by=current_user.id,
        actual_end_date=_parse_date(data.get('actual_end_date')),
        actual_final_cost=data.get('actual_final_cost'),
        project_results_summary=data.get('project_results_summary'),
        deliverables_status=data.get('deliverables_status'),
        lessons_learned=data.get('lessons_learned'),
        recommendations=data.get('recommendations'),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': closure.id, 'closure_status': closure.closure_status}), 201


@integration_bp.route('/<int:project_id>/closure/<int:closure_id>/complete', methods=['POST'])
@login_required
def complete_project(project_id: int, closure_id: int):
    """Mark a closure document as completed."""
    closure, error = ProjectIntegrationService.complete_project(
        closure_id=closure_id,
        approved_by=current_user.id,
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': closure.id, 'closure_status': closure.closure_status})


@integration_bp.route('/<int:project_id>/lessons-learned', methods=['GET'])
@login_required
def get_lessons_learned(project_id: int):
    """Return lessons learned from the most recent closure."""
    lessons = ProjectIntegrationService.get_lessons_learned(project_id)
    if lessons is None:
        return jsonify({'error': 'No closure found for this project'}), 404
    return jsonify({'project_id': project_id, 'lessons_learned': lessons})
