"""Tests for project functionality."""
import pytest
from decimal import Decimal
from app import db as _db
from app.models.project import Project
from app.models.import_log import ImportLog
from app.models.user import User
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


@pytest.fixture(scope='function')
def projects_admin_user(app, db):
    """Create an admin user for projects route tests."""
    with app.app_context():
        user = User(username='proj_admin', email='proj_admin@example.com', role='admin')
        user.set_password('adminpass')
        _db.session.add(user)
        _db.session.commit()
        yield user
        u = _db.session.get(User, user.id)
        if u:
            _db.session.delete(u)
            _db.session.commit()


@pytest.fixture(scope='function')
def projects_logged_in_client(app, db, projects_admin_user):
    """Create an authenticated test client for projects route tests."""
    with app.test_client() as client:
        client.post('/login', data={
            'username': projects_admin_user.username,
            'password': 'adminpass',
        })
        yield client


@pytest.fixture(scope='function')
def index_project(app, db, projects_admin_user):
    """Create a project for index route tests and clean up afterwards."""
    with app.app_context():
        project = Project(
            name='Test Index Project',
            owner_id=projects_admin_user.id,
            status='planning',
            budget=Decimal('5000.00'),
        )
        _db.session.add(project)
        _db.session.commit()
        pid = project.id
    yield pid
    with app.app_context():
        p = _db.session.get(Project, pid)
        if p:
            _db.session.delete(p)
            _db.session.commit()


class TestProjectsIndexRoute:
    """Tests for the /projects/ listing route."""

    def test_projects_index_requires_auth(self, client):
        """Test that /projects/ redirects unauthenticated users."""
        response = client.get('/projects/')
        assert response.status_code == 302

    def test_projects_index_returns_200_for_admin(self, projects_logged_in_client):
        """Test that /projects/ returns 200 for an authenticated admin user."""
        response = projects_logged_in_client.get('/projects/')
        assert response.status_code == 200

    def test_projects_index_shows_project_list(self, projects_logged_in_client, index_project):
        """Test that /projects/ renders the project list without errors."""
        response = projects_logged_in_client.get('/projects/')
        assert response.status_code == 200
        assert b'Test Index Project' in response.data

    def test_projects_index_empty_state(self, projects_logged_in_client):
        """Test that /projects/ renders without errors (regardless of project count)."""
        response = projects_logged_in_client.get('/projects/')
        assert response.status_code == 200
        # The page title should always be present
        assert b'Meus Projetos' in response.data
