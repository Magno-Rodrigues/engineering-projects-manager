"""Stakeholder service for PMBOK Stakeholder Knowledge Area."""
from typing import List, Optional, Tuple
from app import db
from app.models.project import Project
from app.models.stakeholder import Stakeholder, INTEREST_LEVELS, INFLUENCE_LEVELS, STAKEHOLDER_CATEGORIES


class StakeholderService:
    """Business logic for PMBOK Stakeholder Knowledge Area."""

    @staticmethod
    def create_stakeholder(
        project_id: int,
        name: str,
        role: str = None,
        organization: str = None,
        email: str = None,
        phone: str = None,
        interest_level: str = 'medium',
        influence_level: str = 'medium',
        category: str = 'other',
        engagement_strategy: str = None,
        communication_preference: str = None,
        notes: str = None,
    ) -> Tuple[Optional[Stakeholder], Optional[str]]:
        """Create a new stakeholder for a project.

        Returns:
            A tuple of (Stakeholder, None) on success or (None, error_message) on failure.
        """
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not name:
            return None, 'Stakeholder name is required.'
        if interest_level not in INTEREST_LEVELS:
            return None, f'Invalid interest level. Must be one of: {", ".join(INTEREST_LEVELS)}.'
        if influence_level not in INFLUENCE_LEVELS:
            return None, f'Invalid influence level. Must be one of: {", ".join(INFLUENCE_LEVELS)}.'
        if category not in STAKEHOLDER_CATEGORIES:
            return None, f'Invalid category. Must be one of: {", ".join(STAKEHOLDER_CATEGORIES)}.'

        stakeholder = Stakeholder(
            project_id=project_id,
            name=name,
            role=role,
            organization=organization,
            email=email,
            phone=phone,
            interest_level=interest_level,
            influence_level=influence_level,
            category=category,
            engagement_strategy=engagement_strategy,
            communication_preference=communication_preference,
            notes=notes,
        )
        db.session.add(stakeholder)
        db.session.commit()
        return stakeholder, None

    @staticmethod
    def get_project_stakeholders(project_id: int) -> List[Stakeholder]:
        """Return all stakeholders for a project."""
        return Stakeholder.query.filter_by(project_id=project_id).order_by(Stakeholder.name).all()

    @staticmethod
    def get_stakeholder(stakeholder_id: int) -> Optional[Stakeholder]:
        """Return a stakeholder by ID."""
        return db.session.get(Stakeholder, stakeholder_id)

    @staticmethod
    def delete_stakeholder(stakeholder_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a stakeholder.

        Returns:
            A tuple of (True, None) on success or (False, error_message) on failure.
        """
        stakeholder = db.session.get(Stakeholder, stakeholder_id)
        if not stakeholder:
            return False, 'Stakeholder not found.'
        db.session.delete(stakeholder)
        db.session.commit()
        return True, None
