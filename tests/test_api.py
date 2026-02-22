"""Tests for API routes."""
import pytest
from app import db as _db
from app.models.user import User
from app.models.project import Project


@pytest.fixture(scope='function')
def api_user(app, db):
    """Create a user for API tests."""
    with app.app_context():
        user = User(username='apiuser', email='api@example.com')
        user.set_password('apipass123')
        _db.session.add(user)
        _db.session.commit()
        yield user
        _db.session.delete(user)
        _db.session.commit()


@pytest.fixture(scope='function')
def logged_in_client(app, db, api_user):
    """Create an authenticated test client."""
    with app.test_client() as client:
        client.post('/login', data={'username': 'apiuser', 'password': 'apipass123'})
        yield client


class TestAPIProjects:
    """Tests for /api/projects endpoints."""

    def test_get_projects_requires_auth(self, client):
        """Test that /api/projects returns 302 for unauthenticated users."""
        response = client.get('/api/projects')
        assert response.status_code == 302

    def test_get_projects_authenticated(self, logged_in_client):
        """Test that /api/projects returns 200 and a list for authenticated users."""
        response = logged_in_client.get('/api/projects')
        assert response.status_code == 200
        assert response.is_json
        assert isinstance(response.get_json(), list)

    def test_get_project_not_found(self, logged_in_client):
        """Test that /api/projects/<id> returns 404 for unknown projects."""
        response = logged_in_client.get('/api/projects/99999')
        assert response.status_code == 404

    def test_get_project_forbidden(self, app, db, logged_in_client, api_user):
        """Test that accessing another user's project returns 403."""
        with app.app_context():
            other_user = User(username='otherapi', email='other@api.com')
            other_user.set_password('pass')
            _db.session.add(other_user)
            _db.session.flush()
            project = Project(name='Other Project', owner_id=other_user.id)
            _db.session.add(project)
            _db.session.commit()
            project_id = project.id

        response = logged_in_client.get(f'/api/projects/{project_id}')
        assert response.status_code == 403
