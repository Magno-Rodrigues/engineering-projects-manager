"""Scope routes for PMBOK Scope Knowledge Area."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.scope_service import ScopeService
from app.utils.parse_helpers import parse_date as _parse_date

scope_bp = Blueprint('scope', __name__, url_prefix='/projects')


# ---------------------------------------------------------------------------
# Requirement endpoints
# ---------------------------------------------------------------------------

@scope_bp.route('/<int:project_id>/requirements', methods=['GET'])
@login_required
def get_requirements(project_id: int):
    """Return all requirements for a project."""
    requirements = ScopeService.get_project_requirements(project_id)
    return jsonify([
        {
            'id': r.id,
            'requirement_id': r.requirement_id,
            'title': r.title,
            'description': r.description,
            'category': r.category,
            'priority': r.priority,
            'status': r.status,
            'acceptance_criteria': r.acceptance_criteria,
            'source': r.source,
            'trace_to_wbs_items': r.trace_to_wbs_items,
            'created_by': r.created_by,
            'created_at': r.created_at.isoformat(),
            'updated_at': r.updated_at.isoformat(),
        }
        for r in requirements
    ])


@scope_bp.route('/<int:project_id>/requirements', methods=['POST'])
@login_required
def create_requirement(project_id: int):
    """Create a new requirement for a project."""
    data = request.get_json(silent=True) or {}
    requirement, error = ScopeService.create_requirement(
        project_id=project_id,
        created_by=current_user.id,
        requirement_id=data.get('requirement_id', ''),
        title=data.get('title', ''),
        description=data.get('description'),
        category=data.get('category', 'functional'),
        priority=data.get('priority', 'medium'),
        acceptance_criteria=data.get('acceptance_criteria'),
        source=data.get('source'),
        trace_to_wbs_items=data.get('trace_to_wbs_items'),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': requirement.id, 'status': requirement.status}), 201


@scope_bp.route('/<int:project_id>/requirements/<int:requirement_id>/approve', methods=['POST'])
@login_required
def approve_requirement(project_id: int, requirement_id: int):
    """Approve a requirement."""
    requirement, error = ScopeService.approve_requirement(requirement_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': requirement.id, 'status': requirement.status})


# ---------------------------------------------------------------------------
# WBS endpoints
# ---------------------------------------------------------------------------

@scope_bp.route('/<int:project_id>/wbs', methods=['GET'])
@login_required
def get_wbs(project_id: int):
    """Return all WBS items for a project."""
    items = ScopeService.get_project_wbs(project_id)
    return jsonify([
        {
            'id': item.id,
            'wbs_code': item.wbs_code,
            'title': item.title,
            'description': item.description,
            'level': item.level,
            'parent_id': item.parent_id,
            'status': item.status,
            'estimated_effort': str(item.estimated_effort) if item.estimated_effort is not None else None,
            'actual_effort': str(item.actual_effort) if item.actual_effort is not None else None,
            'responsible_user_id': item.responsible_user_id,
            'created_by': item.created_by,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }
        for item in items
    ])


@scope_bp.route('/<int:project_id>/wbs', methods=['POST'])
@login_required
def create_wbs_item(project_id: int):
    """Create a new WBS item for a project."""
    data = request.get_json(silent=True) or {}
    item, error = ScopeService.create_wbs_item(
        project_id=project_id,
        created_by=current_user.id,
        wbs_code=data.get('wbs_code', ''),
        title=data.get('title', ''),
        description=data.get('description'),
        level=data.get('level', 1),
        parent_id=data.get('parent_id'),
        estimated_effort=data.get('estimated_effort'),
        actual_effort=data.get('actual_effort'),
        responsible_user_id=data.get('responsible_user_id'),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': item.id, 'status': item.status}), 201


@scope_bp.route('/<int:project_id>/wbs/effort', methods=['GET'])
@login_required
def get_wbs_effort(project_id: int):
    """Return total WBS effort for a project."""
    effort = ScopeService.calculate_wbs_effort(project_id)
    return jsonify({
        'project_id': project_id,
        'estimated_effort': str(effort['estimated_effort']),
        'actual_effort': str(effort['actual_effort']),
    })


# ---------------------------------------------------------------------------
# Scope change endpoints
# ---------------------------------------------------------------------------

@scope_bp.route('/<int:project_id>/scope-changes', methods=['GET'])
@login_required
def get_scope_changes(project_id: int):
    """Return all scope changes for a project."""
    from app.models.scope_change import ScopeChange
    changes = ScopeChange.query.filter_by(project_id=project_id).all()
    return jsonify([
        {
            'id': c.id,
            'change_id': c.change_id,
            'title': c.title,
            'description': c.description,
            'justification': c.justification,
            'impact_analysis': c.impact_analysis,
            'status': c.status,
            'change_type': c.change_type,
            'affected_requirements': c.affected_requirements,
            'affected_wbs_items': c.affected_wbs_items,
            'requested_by': c.requested_by,
            'approved_by': c.approved_by,
            'approval_date': c.approval_date.isoformat() if c.approval_date else None,
            'created_at': c.created_at.isoformat(),
            'updated_at': c.updated_at.isoformat(),
        }
        for c in changes
    ])


@scope_bp.route('/<int:project_id>/scope-changes', methods=['POST'])
@login_required
def create_scope_change(project_id: int):
    """Create a new scope change request for a project."""
    data = request.get_json(silent=True) or {}
    scope_change, error = ScopeService.create_scope_change(
        project_id=project_id,
        requested_by=current_user.id,
        change_id=data.get('change_id', ''),
        title=data.get('title', ''),
        description=data.get('description'),
        justification=data.get('justification'),
        impact_analysis=data.get('impact_analysis'),
        change_type=data.get('change_type', 'addition'),
        affected_requirements=data.get('affected_requirements'),
        affected_wbs_items=data.get('affected_wbs_items'),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': scope_change.id, 'status': scope_change.status}), 201


@scope_bp.route('/<int:project_id>/scope-changes/<int:change_id>/approve', methods=['POST'])
@login_required
def approve_scope_change(project_id: int, change_id: int):
    """Approve or reject a scope change request."""
    data = request.get_json(silent=True) or {}
    approved = data.get('approved', True)
    scope_change, error = ScopeService.approve_scope_change(
        scope_change_id=change_id,
        approved_by=current_user.id,
        approved=bool(approved),
        approval_date=_parse_date(data.get('approval_date')),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': scope_change.id, 'status': scope_change.status})


@scope_bp.route('/<int:project_id>/scope-changes/<int:change_id>/impact', methods=['GET'])
@login_required
def get_change_impact(project_id: int, change_id: int):
    """Return impact analysis for a scope change."""
    analysis = ScopeService.get_change_impact_analysis(change_id)
    if analysis is None:
        return jsonify({'error': 'Scope change not found'}), 404
    return jsonify(analysis)
