"""Tests for the email system: token service and welcome email flow."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import g

from app import db
from app.models.user import User


def _create_user(db, username='email_user', email='email_user@example.com', password='pass123'):
    """Helper to create a plain user for token tests."""
    user = User(username=username, email=email, full_name='Email User')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _create_admin(db, username='email_admin', email='email_admin@example.com'):
    """Helper to create an admin user."""
    admin = User(username=username, email=email, role='admin')
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return username


class TestTokenService:
    """Tests for TokenService token generation and validation."""

    def test_generate_reset_token_sets_fields(self, app, db):
        """generate_reset_token sets reset_token and expiry on the user."""
        from app.services.token_service import TokenService, TOKEN_EXPIRY_HOURS
        with app.app_context():
            user = _create_user(db, 'tok_gen', 'tok_gen@example.com')
            token = TokenService.generate_reset_token(user)
            assert token is not None
            assert len(token) > 20
            assert user.reset_token == token
            assert user.reset_token_expires_at is not None
            # Expiry should be ~12h in the future
            expected = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
            diff = abs((user.reset_token_expires_at - expected).total_seconds())
            assert diff < 5, 'Expiry time is not within 5 seconds of expected 12-hour window'
            db.session.delete(user)
            db.session.commit()

    def test_verify_valid_token_returns_user(self, app, db):
        """verify_reset_token returns the user for a valid, unexpired token."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'tok_valid', 'tok_valid@example.com')
            token = TokenService.generate_reset_token(user)
            found_user, error = TokenService.verify_reset_token(token)
            assert error is None
            assert found_user is not None
            assert found_user.id == user.id
            db.session.delete(user)
            db.session.commit()

    def test_verify_expired_token_returns_error(self, app, db):
        """verify_reset_token returns an error for an expired token."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'tok_exp', 'tok_exp@example.com')
            token = TokenService.generate_reset_token(user)
            # Manually expire the token
            user.reset_token_expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.session.commit()
            found_user, error = TokenService.verify_reset_token(token)
            assert found_user is None
            assert error is not None
            db.session.delete(user)
            db.session.commit()

    def test_verify_invalid_token_returns_error(self, app, db):
        """verify_reset_token returns an error for a non-existent token."""
        from app.services.token_service import TokenService
        with app.app_context():
            found_user, error = TokenService.verify_reset_token('totally-invalid-token')
            assert found_user is None
            assert error is not None

    def test_verify_empty_token_returns_error(self, app, db):
        """verify_reset_token returns an error for an empty token."""
        from app.services.token_service import TokenService
        with app.app_context():
            found_user, error = TokenService.verify_reset_token('')
            assert found_user is None
            assert error is not None

    def test_invalidate_reset_token_clears_fields(self, app, db):
        """invalidate_reset_token clears the token and expiry from the user."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'tok_inv', 'tok_inv@example.com')
            TokenService.generate_reset_token(user)
            TokenService.invalidate_reset_token(user)
            assert user.reset_token is None
            assert user.reset_token_expires_at is None
            db.session.delete(user)
            db.session.commit()

    def test_token_is_valid_within_12_hours(self, app, db):
        """A token generated now is still valid 11 hours 59 minutes later."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'tok_12h', 'tok_12h@example.com')
            token = TokenService.generate_reset_token(user)
            # Simulate time almost at expiry (1 minute before)
            user.reset_token_expires_at = datetime.utcnow() + timedelta(minutes=1)
            db.session.commit()
            found_user, error = TokenService.verify_reset_token(token)
            assert error is None
            assert found_user is not None
            db.session.delete(user)
            db.session.commit()


class TestEmailService:
    """Tests for EmailService welcome email sending."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_send_welcome_email_called_on_create(self, client, app, db):
        """Welcome email is attempted when admin creates a new user."""
        _create_admin(db, 'email_adm1', 'email_adm1@example.com')
        with patch('app.services.token_service.TokenService.generate_reset_token', return_value='test-token-abc') as mock_token, \
             patch('app.services.email_service.EmailService.send_welcome_email', return_value=True) as mock_send:
            client.post('/login', data={'username': 'email_adm1', 'password': 'adminpass'})
            client.post('/admin/usuarios/novo', data={
                'username': 'welcome_user',
                'email': 'welcome_user@example.com',
                'password': 'pass123',
                'full_name': 'Welcome User',
                'role': 'engineer',
                'key': 'WELKEY',
                'status': 'Ativo',
            })
            mock_token.assert_called_once()
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == 'welcome_user@example.com'

    def test_email_failure_does_not_break_user_creation(self, client, app, db):
        """If email sending fails, the user is still created successfully."""
        _create_admin(db, 'email_adm2', 'email_adm2@example.com')
        with patch('app.services.email_service.EmailService.send_welcome_email', side_effect=Exception('SMTP error')):
            client.post('/login', data={'username': 'email_adm2', 'password': 'adminpass'})
            response = client.post('/admin/usuarios/novo', data={
                'username': 'failmail_user',
                'email': 'failmail_user@example.com',
                'password': 'pass123',
                'full_name': 'Fail Mail User',
                'role': 'engineer',
                'key': 'FAILKEY',
                'status': 'Ativo',
            })
            # Should redirect on success (302), not show an error
            assert response.status_code == 302
            created = User.query.filter_by(username='failmail_user').first()
            assert created is not None


class TestResetPasswordRoutes:
    """Tests for the password reset flow."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_reset_password_get_with_invalid_token_redirects(self, client, app, db):
        """GET /reset-password with invalid token redirects to login with error."""
        response = client.get('/reset-password?token=badtoken')
        assert response.status_code == 302

    def test_reset_password_get_with_valid_token_shows_form(self, client, app, db):
        """GET /reset-password with valid token renders the reset form."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'reset_u1', 'reset_u1@example.com')
            token = TokenService.generate_reset_token(user)
        response = client.get(f'/reset-password?token={token}')
        assert response.status_code == 200
        assert b'Definir nova senha' in response.data or b'nova senha' in response.data.lower()

    def test_reset_password_post_updates_password(self, client, app, db):
        """POST /reset-password with valid token updates the user password."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'reset_u2', 'reset_u2@example.com', 'oldpassword')
            token = TokenService.generate_reset_token(user)
            user_id = user.id
        response = client.post('/reset-password', data={
            'token': token,
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        assert response.status_code == 302
        with app.app_context():
            updated = db.session.get(User, user_id)
            assert updated.check_password('newpassword123')
            assert updated.reset_token is None

    def test_reset_password_post_mismatched_passwords_shows_error(self, client, app, db):
        """POST /reset-password with mismatched passwords re-renders the form."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'reset_u3', 'reset_u3@example.com')
            token = TokenService.generate_reset_token(user)
        response = client.post('/reset-password', data={
            'token': token,
            'password': 'newpassword123',
            'confirm_password': 'differentpassword',
        })
        assert response.status_code == 200

    def test_reset_password_post_expired_token_redirects(self, client, app, db):
        """POST /reset-password with expired token redirects to login."""
        from app.services.token_service import TokenService
        with app.app_context():
            user = _create_user(db, 'reset_u4', 'reset_u4@example.com')
            token = TokenService.generate_reset_token(user)
            user.reset_token_expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.session.commit()
        response = client.post('/reset-password', data={
            'token': token,
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        assert response.status_code == 302
