"""Project Integration service (PMBOK Integration Knowledge Area)."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Any
from app import db
from app.models.project import Project
from app.models.project_charter import ProjectCharter
from app.models.project_closure import ProjectClosure

CHARTER_STATUSES = ('draft', 'approved', 'rejected')
CLOSURE_STATUSES = ('draft', 'completed', 'archived')


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


class ProjectIntegrationService:
    """Business logic for PMBOK Integration Knowledge Area."""

    # ------------------------------------------------------------------
    # Charter (TAP) operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_charter(
        project_id: int,
        created_by: int,
        business_case: str = None,
        project_purpose: str = None,
        success_criteria=None,
        high_level_requirements=None,
        high_level_risks=None,
        assumptions=None,
        constraints=None,
        approved_budget=None,
        scheduled_start_date: date = None,
        scheduled_end_date: date = None,
    ) -> Tuple[Optional[ProjectCharter], Optional[str]]:
        """Create a new Project Charter (TAP).

        Returns:
            A tuple of (ProjectCharter, None) on success or (None, error_message) on failure.
        """
        if not Project.query.get(project_id):
            return None, 'Project not found.'

        budget_val, err = _parse_decimal(approved_budget)
        if err:
            return None, f'Approved budget: {err}'

        if scheduled_start_date and scheduled_end_date and scheduled_end_date < scheduled_start_date:
            return None, 'Scheduled end date cannot be before scheduled start date.'

        charter = ProjectCharter(
            project_id=project_id,
            created_by=created_by,
            business_case=business_case,
            project_purpose=project_purpose,
            success_criteria=success_criteria,
            high_level_requirements=high_level_requirements,
            high_level_risks=high_level_risks,
            assumptions=assumptions,
            constraints=constraints,
            approved_budget=budget_val,
            scheduled_start_date=scheduled_start_date,
            scheduled_end_date=scheduled_end_date,
            status='draft',
        )
        db.session.add(charter)
        db.session.commit()
        return charter, None

    @staticmethod
    def get_charter(project_id: int) -> Optional[ProjectCharter]:
        """Return the most recent charter for a project."""
        return (
            ProjectCharter.query
            .filter_by(project_id=project_id)
            .order_by(ProjectCharter.created_at.desc())
            .first()
        )

    @staticmethod
    def approve_charter(
        charter_id: int,
        authorized_by: int,
        approved: bool = True,
        approval_date: date = None,
    ) -> Tuple[Optional[ProjectCharter], Optional[str]]:
        """Approve or reject a Project Charter.

        Returns:
            A tuple of (ProjectCharter, None) on success or (None, error_message) on failure.
        """
        charter = ProjectCharter.query.get(charter_id)
        if not charter:
            return None, 'Charter not found.'
        if charter.status != 'draft':
            return None, 'Only draft charters can be approved or rejected.'

        charter.status = 'approved' if approved else 'rejected'
        charter.authorized_by = authorized_by
        charter.approval_date = approval_date or date.today()
        db.session.commit()
        return charter, None

    # ------------------------------------------------------------------
    # Closure operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_closure(
        project_id: int,
        created_by: int,
        actual_end_date: date = None,
        actual_final_cost=None,
        project_results_summary: str = None,
        deliverables_status=None,
        lessons_learned: str = None,
        recommendations: str = None,
    ) -> Tuple[Optional[ProjectClosure], Optional[str]]:
        """Create a Project Closure document.

        Returns:
            A tuple of (ProjectClosure, None) on success or (None, error_message) on failure.
        """
        if not Project.query.get(project_id):
            return None, 'Project not found.'

        cost_val, err = _parse_decimal(actual_final_cost)
        if err:
            return None, f'Actual final cost: {err}'

        closure = ProjectClosure(
            project_id=project_id,
            created_by=created_by,
            actual_end_date=actual_end_date,
            actual_final_cost=cost_val,
            project_results_summary=project_results_summary,
            deliverables_status=deliverables_status,
            lessons_learned=lessons_learned,
            recommendations=recommendations,
            closure_status='draft',
        )
        db.session.add(closure)
        db.session.commit()
        return closure, None

    @staticmethod
    def complete_project(
        closure_id: int,
        approved_by: int,
    ) -> Tuple[Optional[ProjectClosure], Optional[str]]:
        """Mark a closure document as completed.

        Returns:
            A tuple of (ProjectClosure, None) on success or (None, error_message) on failure.
        """
        closure = ProjectClosure.query.get(closure_id)
        if not closure:
            return None, 'Closure not found.'
        if closure.closure_status != 'draft':
            return None, 'Only draft closures can be completed.'

        closure.closure_status = 'completed'
        closure.approved_by = approved_by
        db.session.commit()
        return closure, None

    @staticmethod
    def get_lessons_learned(project_id: int) -> Optional[str]:
        """Return lessons learned text from the most recent closure for a project."""
        closure = (
            ProjectClosure.query
            .filter_by(project_id=project_id)
            .order_by(ProjectClosure.created_at.desc())
            .first()
        )
        return closure.lessons_learned if closure else None
