"""Scope management service (PMBOK - Escopo)."""
from typing import List, Optional, Tuple, Dict, Any
from app import db
from app.models.scope import Requirement, WBSItem, ScopeChange


class ScopeService:
    """Service class for scope management operations."""

    # -------------------------
    # Requirements
    # -------------------------

    @staticmethod
    def get_requirements(project_id: int) -> List[Requirement]:
        """Return all requirements for a project."""
        return Requirement.query.filter_by(project_id=project_id).all()

    @staticmethod
    def get_requirement(requirement_id: int) -> Optional[Requirement]:
        """Return a requirement by ID."""
        return db.session.get(Requirement, requirement_id)

    @staticmethod
    def create_requirement(
        project_id: int,
        title: str,
        description: str = None,
        acceptance_criteria: str = None,
        status: str = 'draft',
        priority: str = 'medium',
        created_by: int = None,
    ) -> Tuple[Optional[Requirement], Optional[str]]:
        """Create a new requirement."""
        if not title:
            return None, 'Title is required.'
        req = Requirement(
            project_id=project_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            status=status or 'draft',
            priority=priority or 'medium',
            created_by=created_by,
        )
        db.session.add(req)
        db.session.commit()
        return req, None

    @staticmethod
    def update_requirement(
        requirement_id: int,
        data: Dict[str, Any],
        updated_by: int = None,
    ) -> Tuple[Optional[Requirement], Optional[str]]:
        """Update an existing requirement."""
        req = db.session.get(Requirement, requirement_id)
        if not req:
            return None, 'Requirement not found.'
        allowed_fields = {'title', 'description', 'acceptance_criteria', 'status', 'priority'}
        for key, value in data.items():
            if key in allowed_fields:
                setattr(req, key, value if value != '' else None)
        if not req.title:
            db.session.rollback()
            return None, 'Title is required.'
        req.updated_by = updated_by
        db.session.commit()
        return req, None

    @staticmethod
    def delete_requirement(requirement_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a requirement."""
        req = db.session.get(Requirement, requirement_id)
        if not req:
            return False, 'Requirement not found.'
        db.session.delete(req)
        db.session.commit()
        return True, None

    # -------------------------
    # WBS Items
    # -------------------------

    @staticmethod
    def get_wbs_items(project_id: int) -> List[WBSItem]:
        """Return all WBS items for a project."""
        return WBSItem.query.filter_by(project_id=project_id).order_by(WBSItem.code).all()

    @staticmethod
    def get_wbs_item(wbs_item_id: int) -> Optional[WBSItem]:
        """Return a WBS item by ID."""
        return db.session.get(WBSItem, wbs_item_id)

    @staticmethod
    def create_wbs_item(
        project_id: int,
        title: str,
        code: str = None,
        description: str = None,
        parent_id: int = None,
        created_by: int = None,
    ) -> Tuple[Optional[WBSItem], Optional[str]]:
        """Create a new WBS item."""
        if not title:
            return None, 'Title is required.'
        level = 1
        if parent_id:
            parent = db.session.get(WBSItem, parent_id)
            if not parent:
                return None, 'Parent WBS item not found.'
            if parent.project_id != project_id:
                return None, 'Parent item belongs to a different project.'
            level = parent.level + 1
        item = WBSItem(
            project_id=project_id,
            title=title,
            code=code,
            description=description,
            parent_id=parent_id,
            level=level,
            created_by=created_by,
        )
        db.session.add(item)
        db.session.commit()
        return item, None

    @staticmethod
    def delete_wbs_item(wbs_item_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a WBS item."""
        item = db.session.get(WBSItem, wbs_item_id)
        if not item:
            return False, 'WBS item not found.'
        db.session.delete(item)
        db.session.commit()
        return True, None

    # -------------------------
    # Scope Changes
    # -------------------------

    @staticmethod
    def get_scope_changes(project_id: int) -> List[ScopeChange]:
        """Return all scope changes for a project."""
        return ScopeChange.query.filter_by(project_id=project_id).all()

    @staticmethod
    def get_scope_change(scope_change_id: int) -> Optional[ScopeChange]:
        """Return a scope change by ID."""
        return db.session.get(ScopeChange, scope_change_id)

    @staticmethod
    def create_scope_change(
        project_id: int,
        title: str,
        description: str = None,
        reason: str = None,
        impact: str = None,
        created_by: int = None,
    ) -> Tuple[Optional[ScopeChange], Optional[str]]:
        """Create a new scope change request."""
        if not title:
            return None, 'Title is required.'
        change = ScopeChange(
            project_id=project_id,
            title=title,
            description=description,
            reason=reason,
            impact=impact,
            status='pending',
            requested_by=created_by,
            created_by=created_by,
        )
        db.session.add(change)
        db.session.commit()
        return change, None

    @staticmethod
    def approve_scope_change(
        scope_change_id: int,
        approved_by: int,
    ) -> Tuple[Optional[ScopeChange], Optional[str]]:
        """Approve a scope change."""
        from datetime import datetime
        change = db.session.get(ScopeChange, scope_change_id)
        if not change:
            return None, 'Scope change not found.'
        if change.status != 'pending':
            return None, 'Only pending scope changes can be approved.'
        change.status = 'approved'
        change.approved_by = approved_by
        change.approved_at = datetime.utcnow()
        db.session.commit()
        return change, None

    @staticmethod
    def reject_scope_change(
        scope_change_id: int,
        updated_by: int,
    ) -> Tuple[Optional[ScopeChange], Optional[str]]:
        """Reject a scope change."""
        change = db.session.get(ScopeChange, scope_change_id)
        if not change:
            return None, 'Scope change not found.'
        if change.status != 'pending':
            return None, 'Only pending scope changes can be rejected.'
        change.status = 'rejected'
        change.updated_by = updated_by
        db.session.commit()
        return change, None

    @staticmethod
    def delete_scope_change(scope_change_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a scope change."""
        change = db.session.get(ScopeChange, scope_change_id)
        if not change:
            return False, 'Scope change not found.'
        db.session.delete(change)
        db.session.commit()
        return True, None
