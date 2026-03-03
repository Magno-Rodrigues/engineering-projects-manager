"""Scope service for PMBOK Scope Knowledge Area."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Any
from app import db
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.wbs_item import WBSItem
from app.models.scope_change import ScopeChange

REQUIREMENT_CATEGORIES = ('functional', 'non-functional', 'business', 'technical')
REQUIREMENT_PRIORITIES = ('critical', 'high', 'medium', 'low')
REQUIREMENT_STATUSES = ('draft', 'approved', 'implemented', 'closed')

WBS_STATUSES = ('planning', 'in_progress', 'completed', 'cancelled')

SCOPE_CHANGE_STATUSES = ('draft', 'submitted', 'approved', 'rejected', 'implemented')
SCOPE_CHANGE_TYPES = ('addition', 'deletion', 'modification')


def _parse_decimal(value: Any) -> Tuple[Optional[Decimal], Optional[str]]:
    """Parse a decimal value.

    Returns:
        A tuple of (Decimal, None) on success or (None, error_message) on failure.
    """
    if value is None or value == '':
        return None, None
    try:
        result = Decimal(str(value))
        if result < 0:
            return None, 'Value cannot be negative.'
        return result, None
    except InvalidOperation:
        return None, 'Invalid numeric value.'


class ScopeService:
    """Business logic for PMBOK Scope Knowledge Area."""

    # ------------------------------------------------------------------
    # Requirement operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_requirement(
        project_id: int,
        created_by: int,
        requirement_id: str,
        title: str,
        description: str = None,
        category: str = 'functional',
        priority: str = 'medium',
        acceptance_criteria=None,
        source: str = None,
        trace_to_wbs_items=None,
    ) -> Tuple[Optional[Requirement], Optional[str]]:
        """Create a new requirement.

        Returns:
            A tuple of (Requirement, None) on success or (None, error_message) on failure.
        """
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not title:
            return None, 'Requirement title is required.'
        if not requirement_id:
            return None, 'Requirement ID is required.'
        if category not in REQUIREMENT_CATEGORIES:
            return None, f'Invalid category. Must be one of: {", ".join(REQUIREMENT_CATEGORIES)}.'
        if priority not in REQUIREMENT_PRIORITIES:
            return None, f'Invalid priority. Must be one of: {", ".join(REQUIREMENT_PRIORITIES)}.'
        if Requirement.query.filter_by(requirement_id=requirement_id).first():
            return None, 'Requirement ID already exists.'

        requirement = Requirement(
            project_id=project_id,
            created_by=created_by,
            requirement_id=requirement_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status='draft',
            acceptance_criteria=acceptance_criteria,
            source=source,
            trace_to_wbs_items=trace_to_wbs_items,
        )
        db.session.add(requirement)
        db.session.commit()
        return requirement, None

    @staticmethod
    def approve_requirement(
        requirement_id: int,
    ) -> Tuple[Optional[Requirement], Optional[str]]:
        """Approve a requirement.

        Returns:
            A tuple of (Requirement, None) on success or (None, error_message) on failure.
        """
        requirement = db.session.get(Requirement, requirement_id)
        if not requirement:
            return None, 'Requirement not found.'
        if requirement.status != 'draft':
            return None, 'Only draft requirements can be approved.'
        requirement.status = 'approved'
        db.session.commit()
        return requirement, None

    @staticmethod
    def get_project_requirements(project_id: int) -> List[Requirement]:
        """Return all requirements for a project."""
        return Requirement.query.filter_by(project_id=project_id).all()

    # ------------------------------------------------------------------
    # WBS operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_wbs_item(
        project_id: int,
        created_by: int,
        wbs_code: str,
        title: str,
        description: str = None,
        level: int = 1,
        parent_id: int = None,
        estimated_effort=None,
        actual_effort=None,
        responsible_user_id: int = None,
    ) -> Tuple[Optional[WBSItem], Optional[str]]:
        """Create a new WBS item.

        Returns:
            A tuple of (WBSItem, None) on success or (None, error_message) on failure.
        """
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not title:
            return None, 'WBS item title is required.'
        if not wbs_code:
            return None, 'WBS code is required.'

        est_val, err = _parse_decimal(estimated_effort)
        if err:
            return None, f'Estimated effort: {err}'
        act_val, err = _parse_decimal(actual_effort)
        if err:
            return None, f'Actual effort: {err}'

        if parent_id is not None and not db.session.get(WBSItem, parent_id):
            return None, 'Parent WBS item not found.'

        item = WBSItem(
            project_id=project_id,
            created_by=created_by,
            wbs_code=wbs_code,
            title=title,
            description=description,
            level=level,
            parent_id=parent_id,
            status='planning',
            estimated_effort=est_val,
            actual_effort=act_val,
            responsible_user_id=responsible_user_id,
        )
        db.session.add(item)
        db.session.commit()
        return item, None

    @staticmethod
    def get_project_wbs(project_id: int) -> List[WBSItem]:
        """Return all WBS items for a project ordered by wbs_code."""
        return WBSItem.query.filter_by(project_id=project_id).order_by(WBSItem.wbs_code).all()

    @staticmethod
    def calculate_wbs_effort(project_id: int) -> dict:
        """Calculate total estimated and actual effort for a project's WBS.

        Returns:
            A dict with 'estimated_effort' and 'actual_effort' totals.
        """
        items = WBSItem.query.filter_by(project_id=project_id).all()
        estimated = sum((item.estimated_effort or Decimal('0')) for item in items)
        actual = sum((item.actual_effort or Decimal('0')) for item in items)
        return {
            'estimated_effort': estimated,
            'actual_effort': actual,
        }

    # ------------------------------------------------------------------
    # Scope change operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_scope_change(
        project_id: int,
        requested_by: int,
        change_id: str,
        title: str,
        description: str = None,
        justification: str = None,
        impact_analysis: str = None,
        change_type: str = 'addition',
        affected_requirements=None,
        affected_wbs_items=None,
    ) -> Tuple[Optional[ScopeChange], Optional[str]]:
        """Create a new scope change request.

        Returns:
            A tuple of (ScopeChange, None) on success or (None, error_message) on failure.
        """
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not title:
            return None, 'Scope change title is required.'
        if not change_id:
            return None, 'Change ID is required.'
        if change_type not in SCOPE_CHANGE_TYPES:
            return None, f'Invalid change type. Must be one of: {", ".join(SCOPE_CHANGE_TYPES)}.'
        if ScopeChange.query.filter_by(change_id=change_id).first():
            return None, 'Change ID already exists.'

        scope_change = ScopeChange(
            project_id=project_id,
            requested_by=requested_by,
            change_id=change_id,
            title=title,
            description=description,
            justification=justification,
            impact_analysis=impact_analysis,
            status='draft',
            change_type=change_type,
            affected_requirements=affected_requirements,
            affected_wbs_items=affected_wbs_items,
        )
        db.session.add(scope_change)
        db.session.commit()
        return scope_change, None

    @staticmethod
    def approve_scope_change(
        scope_change_id: int,
        approved_by: int,
        approved: bool = True,
        approval_date: date = None,
    ) -> Tuple[Optional[ScopeChange], Optional[str]]:
        """Approve or reject a scope change request.

        Returns:
            A tuple of (ScopeChange, None) on success or (None, error_message) on failure.
        """
        scope_change = db.session.get(ScopeChange, scope_change_id)
        if not scope_change:
            return None, 'Scope change not found.'
        if scope_change.status not in ('draft', 'submitted'):
            return None, 'Only draft or submitted scope changes can be approved or rejected.'
        scope_change.status = 'approved' if approved else 'rejected'
        scope_change.approved_by = approved_by
        scope_change.approval_date = approval_date or date.today()
        db.session.commit()
        return scope_change, None

    @staticmethod
    def get_change_impact_analysis(scope_change_id: int) -> Optional[dict]:
        """Return impact analysis details for a scope change.

        Returns:
            A dict with impact analysis details or None if not found.
        """
        scope_change = db.session.get(ScopeChange, scope_change_id)
        if not scope_change:
            return None
        return {
            'change_id': scope_change.change_id,
            'title': scope_change.title,
            'impact_analysis': scope_change.impact_analysis,
            'affected_requirements': scope_change.affected_requirements,
            'affected_wbs_items': scope_change.affected_wbs_items,
            'status': scope_change.status,
        }
