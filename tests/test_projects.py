"""Tests for project functionality."""
import pytest
from app.models.project import Project
from app.services.project_service import ProjectService


class TestProjectService:
    """Tests for ProjectService."""

    def test_create_project_missing_name(self, app, db):
        """Test that creating a project without a name returns an error."""
        with app.app_context():
            project, error = ProjectService.create_project(
                name='', description='desc', owner_id=1
            )
            assert project is None
            assert error is not None

    def test_get_nonexistent_project(self, app, db):
        """Test that getting a non-existent project returns None."""
        with app.app_context():
            project = ProjectService.get_project(99999)
            assert project is None

    def test_delete_nonexistent_project(self, app, db):
        """Test that deleting a non-existent project returns an error."""
        with app.app_context():
            success, error = ProjectService.delete_project(99999)
            assert success is False
            assert error is not None


class TestProjectModel:
    """Tests for Project model."""

    def test_project_repr(self, app, db):
        """Test project string representation."""
        with app.app_context():
            project = Project(name='Test Project', owner_id=1)
            assert 'Test Project' in repr(project)
