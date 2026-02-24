"""CommunicationPlan service for PMBOK Communication Knowledge Area."""
from typing import List, Optional, Tuple
from app import db
from app.models.project import Project
from app.models.communication_plan import CommunicationPlan, FREQUENCIES, COMMUNICATION_METHODS, DISTRIBUTION_METHODS


class CommunicationPlanService:
    """Business logic for PMBOK Communication Knowledge Area."""

    @staticmethod
    def create_communication_plan(
        project_id: int,
        created_by: int,
        information: str,
        frequency: str = 'weekly',
        responsible: str = None,
        target_audience: str = None,
        communication_method: str = 'email',
        distribution_method: str = 'direct',
        notes: str = None,
    ) -> Tuple[Optional[CommunicationPlan], Optional[str]]:
        """Create a new communication plan entry for a project.

        Returns:
            A tuple of (CommunicationPlan, None) on success or (None, error_message) on failure.
        """
        if not Project.query.get(project_id):
            return None, 'Project not found.'
        if not information:
            return None, 'Information to be communicated is required.'
        if frequency not in FREQUENCIES:
            return None, f'Invalid frequency. Must be one of: {", ".join(FREQUENCIES)}.'
        if communication_method not in COMMUNICATION_METHODS:
            return None, f'Invalid communication method. Must be one of: {", ".join(COMMUNICATION_METHODS)}.'
        if distribution_method not in DISTRIBUTION_METHODS:
            return None, f'Invalid distribution method. Must be one of: {", ".join(DISTRIBUTION_METHODS)}.'

        plan = CommunicationPlan(
            project_id=project_id,
            created_by=created_by,
            information=information,
            frequency=frequency,
            responsible=responsible,
            target_audience=target_audience,
            communication_method=communication_method,
            distribution_method=distribution_method,
            notes=notes,
        )
        db.session.add(plan)
        db.session.commit()
        return plan, None

    @staticmethod
    def get_project_communication_plans(project_id: int) -> List[CommunicationPlan]:
        """Return all communication plan entries for a project."""
        return CommunicationPlan.query.filter_by(project_id=project_id).order_by(CommunicationPlan.created_at).all()

    @staticmethod
    def delete_communication_plan(plan_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a communication plan entry.

        Returns:
            A tuple of (True, None) on success or (False, error_message) on failure.
        """
        plan = CommunicationPlan.query.get(plan_id)
        if not plan:
            return False, 'Communication plan entry not found.'
        db.session.delete(plan)
        db.session.commit()
        return True, None
