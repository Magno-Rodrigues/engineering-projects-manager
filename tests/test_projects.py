"""Tests for project functionality."""
import pytest
from app.models.project import Project
from app.models.import_log import ImportLog
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

    def test_delete_project_cascades_import_logs(self, app, db):
        """Test that deleting a project also removes its import_logs (no integrity error)."""
        with app.app_context():
            project = Project(name='Project To Delete', owner_id=1)
            db.session.add(project)
            db.session.flush()

            log = ImportLog(
                project_id=project.id,
                import_type='ms_project',
                file_name='test.xml',
                status='success',
            )
            db.session.add(log)
            db.session.commit()

            project_id = project.id
            log_id = log.id

            success, error = ProjectService.delete_project(project_id)
            assert success is True
            assert error is None

            # Expire the session to force a fresh DB read, then confirm the log was removed
            db.session.expire_all()
            assert db.session.get(ImportLog, log_id) is None


class TestProjectModel:
    """Tests for Project model."""

    def test_project_repr(self, app, db):
        """Test project string representation."""
        with app.app_context():
            project = Project(name='Test Project', owner_id=1)
            assert 'Test Project' in repr(project)
