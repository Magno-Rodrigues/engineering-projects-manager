"""Scope management routes (PMBOK - Escopo)."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.services.scope_service import ScopeService

scope_bp = Blueprint('scope', __name__, url_prefix='/projects/<int:project_id>/scope')


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


# -------------------------
# Requirements
# -------------------------

@scope_bp.route('/requirements')
@login_required
def requirements(project_id: int):
    """List requirements for a project."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    reqs = ScopeService.get_requirements(project_id)
    return render_template('scope/requirements.html', project=project, requirements=reqs)


@scope_bp.route('/requirements/new', methods=['GET', 'POST'])
@login_required
def create_requirement(project_id: int):
    """Create a new requirement."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        req, error = ScopeService.create_requirement(
            project_id=project_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            acceptance_criteria=request.form.get('acceptance_criteria'),
            status=request.form.get('status', 'draft'),
            priority=request.form.get('priority', 'medium'),
            created_by=current_user.id,
        )
        if req:
            flash('Requirement created successfully.', 'success')
            return redirect(url_for('scope.requirements', project_id=project_id))
        flash(error, 'error')
    return render_template('scope/requirement_form.html', project=project, requirement=None)


@scope_bp.route('/requirements/<int:req_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_requirement(project_id: int, req_id: int):
    """Edit a requirement."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    req = ScopeService.get_requirement(req_id)
    if not req or req.project_id != project_id:
        flash('Requirement not found.', 'error')
        return redirect(url_for('scope.requirements', project_id=project_id))
    if request.method == 'POST':
        updated, error = ScopeService.update_requirement(
            req_id,
            {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'acceptance_criteria': request.form.get('acceptance_criteria'),
                'status': request.form.get('status'),
                'priority': request.form.get('priority'),
            },
            updated_by=current_user.id,
        )
        if updated:
            flash('Requirement updated successfully.', 'success')
            return redirect(url_for('scope.requirements', project_id=project_id))
        flash(error, 'error')
    return render_template('scope/requirement_form.html', project=project, requirement=req)


@scope_bp.route('/requirements/<int:req_id>/delete', methods=['POST'])
@login_required
def delete_requirement(project_id: int, req_id: int):
    """Delete a requirement."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    ScopeService.delete_requirement(req_id)
    flash('Requirement deleted.', 'success')
    return redirect(url_for('scope.requirements', project_id=project_id))


# -------------------------
# WBS
# -------------------------

@scope_bp.route('/wbs')
@login_required
def wbs(project_id: int):
    """Show WBS for a project."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    items = ScopeService.get_wbs_items(project_id)
    return render_template('scope/wbs.html', project=project, wbs_items=items)


@scope_bp.route('/wbs/new', methods=['GET', 'POST'])
@login_required
def create_wbs_item(project_id: int):
    """Create a new WBS item."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        parent_id = request.form.get('parent_id') or None
        if parent_id:
            parent_id = int(parent_id)
        item, error = ScopeService.create_wbs_item(
            project_id=project_id,
            title=request.form.get('title'),
            code=request.form.get('code'),
            description=request.form.get('description'),
            parent_id=parent_id,
            created_by=current_user.id,
        )
        if item:
            flash('WBS item created successfully.', 'success')
            return redirect(url_for('scope.wbs', project_id=project_id))
        flash(error, 'error')
    all_items = ScopeService.get_wbs_items(project_id)
    return render_template('scope/wbs_form.html', project=project, wbs_items=all_items)


@scope_bp.route('/wbs/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_wbs_item(project_id: int, item_id: int):
    """Delete a WBS item."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    ScopeService.delete_wbs_item(item_id)
    flash('WBS item deleted.', 'success')
    return redirect(url_for('scope.wbs', project_id=project_id))


# -------------------------
# Scope Changes
# -------------------------

@scope_bp.route('/changes')
@login_required
def scope_changes(project_id: int):
    """List scope changes for a project."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    changes = ScopeService.get_scope_changes(project_id)
    return render_template('scope/scope_changes.html', project=project, scope_changes=changes)


@scope_bp.route('/changes/new', methods=['GET', 'POST'])
@login_required
def create_scope_change(project_id: int):
    """Create a new scope change request."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    if request.method == 'POST':
        change, error = ScopeService.create_scope_change(
            project_id=project_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            reason=request.form.get('reason'),
            impact=request.form.get('impact'),
            created_by=current_user.id,
        )
        if change:
            flash('Scope change request created.', 'success')
            return redirect(url_for('scope.scope_changes', project_id=project_id))
        flash(error, 'error')
    return render_template('scope/scope_change_form.html', project=project, scope_change=None)


@scope_bp.route('/changes/<int:change_id>/approve', methods=['POST'])
@login_required
def approve_scope_change(project_id: int, change_id: int):
    """Approve a scope change."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    change, error = ScopeService.approve_scope_change(change_id, approved_by=current_user.id)
    if change:
        flash('Scope change approved.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('scope.scope_changes', project_id=project_id))


@scope_bp.route('/changes/<int:change_id>/reject', methods=['POST'])
@login_required
def reject_scope_change(project_id: int, change_id: int):
    """Reject a scope change."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    change, error = ScopeService.reject_scope_change(change_id, updated_by=current_user.id)
    if change:
        flash('Scope change rejected.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('scope.scope_changes', project_id=project_id))


@scope_bp.route('/changes/<int:change_id>/delete', methods=['POST'])
@login_required
def delete_scope_change(project_id: int, change_id: int):
    """Delete a scope change."""
    project, redir = _get_project_or_abort(project_id)
    if redir:
        return redir
    ScopeService.delete_scope_change(change_id)
    flash('Scope change deleted.', 'success')
    return redirect(url_for('scope.scope_changes', project_id=project_id))
