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

    def test_get_user_projects_exclude_blocked(self, app, db):
        """Test that get_user_projects filters out blocked projects when exclude_blocked=True."""
        with app.app_context():
            active_project, _ = ProjectService.create_project(
                name='Active Project', description='', owner_id=1, status='planning'
            )
            blocked_project, _ = ProjectService.create_project(
                name='Blocked Project', description='', owner_id=1, status='blocked'
            )
            try:
                all_projects = ProjectService.get_user_projects(1, include_all=True, exclude_blocked=False)
                filtered_projects = ProjectService.get_user_projects(1, include_all=True, exclude_blocked=True)

                all_ids = [p.id for p in all_projects]
                filtered_ids = [p.id for p in filtered_projects]

                assert active_project.id in all_ids
                assert blocked_project.id in all_ids
                assert active_project.id in filtered_ids
                assert blocked_project.id not in filtered_ids
            finally:
                db.session.delete(active_project)
                db.session.delete(blocked_project)
                db.session.commit()

    def test_toggle_project_status_blocks_project(self, app, db):
        """Test that toggle_project_status sets a planning project to blocked."""
        with app.app_context():
            project, _ = ProjectService.create_project(
                name='Toggle Test Project', description='', owner_id=1, status='planning'
            )
            try:
                assert project.status == 'planning'
                toggled, error = ProjectService.toggle_project_status(project.id)
                assert error is None
                assert toggled.status == 'blocked'
            finally:
                db.session.delete(project)
                db.session.commit()

    def test_toggle_project_status_unblocks_project(self, app, db):
        """Test that toggle_project_status restores a blocked project to planning."""
        with app.app_context():
            project, _ = ProjectService.create_project(
                name='Unblock Test Project', description='', owner_id=1, status='blocked'
            )
            try:
                assert project.status == 'blocked'
                toggled, error = ProjectService.toggle_project_status(project.id)
                assert error is None
                assert toggled.status == 'planning'
            finally:
                db.session.delete(project)
                db.session.commit()

    def test_toggle_project_status_nonexistent(self, app, db):
        """Test that toggling a non-existent project returns an error."""
        with app.app_context():
            project, error = ProjectService.toggle_project_status(99999)
            assert project is None
            assert error is not None


class TestProjectModel:
    """Tests for Project model."""

    def test_project_repr(self, app, db):
        """Test project string representation."""
        with app.app_context():
            project = Project(name='Test Project', owner_id=1)
            assert 'Test Project' in repr(project)
