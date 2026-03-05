"""Tests for authentication functionality."""
import pytest
from flask import g
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

    def test_register_user_by_admin_success(self, app, db):
        """Test that register_user_by_admin creates a user with the given role."""
        from app.services.auth_service import AuthService
        with app.app_context():
            user, error = AuthService.register_user_by_admin(
                'neweng', 'neweng@example.com', 'pass123', role='engineer', admin_id=1
            )
            assert error is None
            assert user is not None
            assert user.role == 'engineer'
            db.session.delete(user)
            db.session.commit()

    def test_register_user_by_admin_duplicate_username(self, app, db, test_user):
        """Test that duplicate username returns an error."""
        from app.services.auth_service import AuthService
        with app.app_context():
            _, error = AuthService.register_user_by_admin(
                'testuser', 'other@example.com', 'pass123'
            )
            assert error == 'Username already taken.'

    def test_register_user_by_admin_duplicate_email(self, app, db, test_user):
        """Test that duplicate email returns an error."""
        from app.services.auth_service import AuthService
        with app.app_context():
            _, error = AuthService.register_user_by_admin(
                'otherusername', 'test@example.com', 'pass123'
            )
            assert error == 'Email already registered.'


class TestAuthRoutes:
    """Tests for authentication routes."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_login_page_loads(self, client):
        """Test that login page returns 200."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page_requires_login(self, client):
        """Test that anonymous users are redirected away from register page."""
        response = client.get('/register')
        assert response.status_code == 302

    def test_register_page_forbidden_for_non_admin(self, client, app, db):
        """Test that a non-admin user receives 403 on the register page."""
        user = User(username='normaluser2', email='normal2@example.com', role='engineer')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()

        client.post('/login', data={'username': 'normaluser2', 'password': 'pass123'})
        response = client.get('/register')
        assert response.status_code == 403

    def test_register_page_accessible_for_admin(self, client, app, db):
        """Test that an admin user can access the register page."""
        admin = User(username='adminuser2', email='admin2@example.com', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()

        client.post('/login', data={'username': 'adminuser2', 'password': 'adminpass'})
        response = client.get('/register')
        assert response.status_code == 200

    def test_admin_can_register_new_user(self, client, app, db):
        """Test that an admin can POST to /register and create a new user."""
        admin = User(username='adminreg2', email='adminreg2@example.com', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()

        client.post('/login', data={'username': 'adminreg2', 'password': 'adminpass'})
        response = client.post('/register', data={
            'username': 'createdbyAdmin2',
            'email': 'created2@example.com',
            'password': 'pass123',
            'role': 'engineer',
        })
        assert response.status_code == 302

        created = User.query.filter_by(username='createdbyAdmin2').first()
        assert created is not None
        assert created.role == 'engineer'

    def test_logout_requires_login(self, client):
        """Test that logout redirects unauthenticated users."""
        response = client.get('/logout')
        assert response.status_code == 302

    def test_login_redirects_to_reset_when_password_reset_required(self, client, app, db):
        """Test that users with password_reset_required=True are redirected to reset-password."""
        user = User(username='resetuser', email='reset@example.com', password_reset_required=True)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()

        response = client.post('/login', data={'username': 'resetuser', 'password': 'pass123'})
        assert response.status_code == 302
        assert '/reset-password' in response.headers['Location']

        db.session.delete(user)
        db.session.commit()

    def test_login_redirects_to_dashboard_when_no_reset_required(self, client, app, db):
        """Test that normal users are redirected to dashboard after login."""
        user = User(username='normallogin', email='normallogin@example.com', password_reset_required=False)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()

        response = client.post('/login', data={'username': 'normallogin', 'password': 'pass123'})
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

        db.session.delete(user)
        db.session.commit()

    def test_login_respects_safe_next_url(self, client, app, db):
        """Test that a safe relative next URL is used after login."""
        user = User(username='nextuser', email='nextuser@example.com', password_reset_required=False)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()

        response = client.post('/login?next=/projects/', data={'username': 'nextuser', 'password': 'pass123'})
        assert response.status_code == 302
        assert '/projects/' in response.headers['Location']

        db.session.delete(user)
        db.session.commit()

    def test_login_ignores_unsafe_next_url(self, client, app, db):
        """Test that an absolute next URL with a netloc is ignored to prevent open redirect."""
        user = User(username='nextuser2', email='nextuser2@example.com', password_reset_required=False)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()

        response = client.post(
            '/login?next=http://evil.example.com/',
            data={'username': 'nextuser2', 'password': 'pass123'},
        )
        assert response.status_code == 302
        location = response.headers['Location']
        assert 'evil.example.com' not in location
        assert '/dashboard' in location

        db.session.delete(user)
        db.session.commit()
