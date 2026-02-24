"""API routes for JSON responses."""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.services.project_service import ProjectService

api_bp = Blueprint('api', __name__)


@api_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """Return a JSON list of the current user's projects."""
    projects = ProjectService.get_user_projects(current_user.id, include_all=(current_user.role == 'admin'))
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'status': p.status,
    } for p in projects])


@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id: int):
    """Return a JSON representation of a project."""
    project = ProjectService.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    if current_user.role != 'admin' and project.owner_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'status': project.status,
    })
