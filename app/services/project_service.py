"""Project service."""
from typing import List, Optional, Tuple, Dict, Any
from app import db
from app.models.project import Project


class ProjectService:
    """Service class for project operations."""

    @staticmethod
    def get_user_projects(user_id: int) -> List[Project]:
        """Return all projects owned by a user."""
        return Project.query.filter_by(owner_id=user_id).all()

    @staticmethod
    def get_project(project_id: int) -> Optional[Project]:
        """Return a project by ID."""
        return Project.query.get(project_id)

    @staticmethod
    def create_project(name: str, description: str, owner_id: int) -> Tuple[Optional[Project], Optional[str]]:
        """Create a new project.

        Args:
            name: Project name.
            description: Project description.
            owner_id: ID of the owning user.

        Returns:
            A tuple of (Project, None) on success or (None, error_message) on failure.
        """
        if not name:
            return None, 'Project name is required.'
        project = Project(name=name, description=description, owner_id=owner_id)
        db.session.add(project)
        db.session.commit()
        return project, None

    @staticmethod
    def update_project(project_id: int, data: Dict[str, Any]) -> Tuple[Optional[Project], Optional[str]]:
        """Update an existing project.

        Args:
            project_id: ID of the project to update.
            data: Dictionary of fields to update.

        Returns:
            A tuple of (Project, None) on success or (None, error_message) on failure.
        """
        project = Project.query.get(project_id)
        if not project:
            return None, 'Project not found.'
        allowed_fields = {'name', 'description', 'status', 'start_date', 'end_date'}
        for key, value in data.items():
            if key in allowed_fields and value is not None:
                setattr(project, key, value)
        db.session.commit()
        return project, None

    @staticmethod
    def delete_project(project_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a project by ID.

        Returns:
            A tuple of (True, None) on success or (False, error_message) on failure.
        """
        project = Project.query.get(project_id)
        if not project:
            return False, 'Project not found.'
        db.session.delete(project)
        db.session.commit()
        return True, None
