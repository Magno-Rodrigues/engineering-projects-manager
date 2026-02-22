"""Tests for authentication functionality."""
import pytest
from app.models.user import User


class TestAuthService:
    """Tests for AuthService."""

    def test_user_password_hashing(self, app, db):
        """Test that passwords are hashed correctly."""
        with app.app_context():
            user = User(username='hashtest', email='hash@example.com')
            user.set_password('mypassword')
            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False

    def test_user_repr(self, app, db):
        """Test user string representation."""
        with app.app_context():
            user = User(username='reprtest', email='repr@example.com')
            assert 'reprtest' in repr(user)


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test that login page returns 200."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page_loads(self, client):
        """Test that register page returns 200."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_logout_requires_login(self, client):
        """Test that logout redirects unauthenticated users."""
        response = client.get('/logout')
        assert response.status_code == 302
