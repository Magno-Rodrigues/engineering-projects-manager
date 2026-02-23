"""Tests for the hybrid email service."""
import platform
from unittest.mock import MagicMock, call, patch

import pytest


class TestSendEmailRouting:
    """Tests for send_email() transport routing."""

    def test_routes_to_smtp_on_production(self, app):
        """send_email() uses SMTP when ENV=production regardless of OS."""
        with app.app_context():
            app.config['ENV'] = 'production'
            with patch(
                'app.services.email_service._send_via_smtp', return_value=True
            ) as mock_smtp, patch(
                'app.services.email_service._send_via_outlook_auto', return_value=True
            ) as mock_outlook:
                from app.services.email_service import send_email
                send_email('to@example.com', 'Subject', '<p>Body</p>')
                mock_smtp.assert_called_once()
                mock_outlook.assert_not_called()

    def test_routes_to_smtp_on_non_windows_development(self, app):
        """send_email() uses SMTP on non-Windows OS even when ENV=development."""
        with app.app_context():
            app.config['ENV'] = 'development'
            # Simulate a non-Windows OS to ensure the test is deterministic on all platforms
            with patch('platform.system', return_value='Linux'), \
                 patch('app.services.email_service._send_via_smtp', return_value=True) as mock_smtp, \
                 patch('app.services.email_service._send_via_outlook_auto', return_value=True) as mock_outlook:
                from app.services.email_service import send_email
                send_email('to@example.com', 'Subject', '<p>Body</p>')
                mock_smtp.assert_called_once()
                mock_outlook.assert_not_called()

    def test_routes_to_outlook_on_windows_development(self, app):
        """send_email() uses Outlook COM on Windows when ENV=development."""
        with app.app_context():
            app.config['ENV'] = 'development'
            with patch('platform.system', return_value='Windows'), \
                 patch('app.services.email_service._send_via_outlook_auto', return_value=True) as mock_outlook, \
                 patch('app.services.email_service._send_via_smtp', return_value=True) as mock_smtp:
                from app.services.email_service import send_email
                send_email('to@example.com', 'Subject', '<p>Body</p>')
                mock_outlook.assert_called_once()
                mock_smtp.assert_not_called()


class TestSendViaOutlookAuto:
    """Tests for the Outlook COM transport lifecycle."""

    def _make_win32_mocks(self):
        """Return mock objects for win32com.client, win32api, win32con."""
        mock_mail = MagicMock()
        mock_outlook = MagicMock()
        mock_outlook.Session.Accounts.Count = 1
        mock_outlook.Session.Accounts.Item.return_value = MagicMock()
        mock_outlook.CreateItem.return_value = mock_mail

        mock_win32com = MagicMock()
        mock_win32com.client.Dispatch.return_value = mock_outlook
        return mock_win32com, mock_outlook, mock_mail

    def test_creates_fresh_dispatch_each_call(self, app):
        """_send_via_outlook_auto calls Dispatch() on every invocation."""
        with app.app_context():
            mock_win32com, mock_outlook, mock_mail = self._make_win32_mocks()
            modules = {
                'win32com': mock_win32com,
                'win32com.client': mock_win32com.client,
                'win32api': MagicMock(),
                'win32con': MagicMock(),
            }
            with patch.dict('sys.modules', modules), \
                 patch('app.services.email_service._dismiss_outlook_security_popup', return_value=True):
                from app.services.email_service import _send_via_outlook_auto
                _send_via_outlook_auto('a@example.com', 'S', '<p>B</p>')
                _send_via_outlook_auto('b@example.com', 'S', '<p>B</p>')
            assert mock_win32com.client.Dispatch.call_count == 2

    def test_releases_com_objects_after_send(self, app):
        """_send_via_outlook_auto triggers gc.collect() after each send."""
        with app.app_context():
            mock_win32com, mock_outlook, mock_mail = self._make_win32_mocks()
            modules = {
                'win32com': mock_win32com,
                'win32com.client': mock_win32com.client,
                'win32api': MagicMock(),
                'win32con': MagicMock(),
            }
            with patch('app.services.email_service.gc.collect') as mock_gc, \
                 patch.dict('sys.modules', modules), \
                 patch('app.services.email_service._dismiss_outlook_security_popup', return_value=True):
                from app.services.email_service import _send_via_outlook_auto
                _send_via_outlook_auto('a@example.com', 'S', '<p>B</p>')
            mock_gc.assert_called_once()

    def test_gc_called_even_on_failure(self, app):
        """gc.collect() is called even when the COM send raises an exception."""
        with app.app_context():
            mock_win32com = MagicMock()
            mock_win32com.client.Dispatch.side_effect = RuntimeError('COM error')
            modules = {
                'win32com': mock_win32com,
                'win32com.client': mock_win32com.client,
                'win32api': MagicMock(),
                'win32con': MagicMock(),
            }
            with patch('app.services.email_service.gc.collect') as mock_gc, \
                 patch('app.services.email_service._send_via_smtp', return_value=False), \
                 patch.dict('sys.modules', modules):
                from app.services.email_service import _send_via_outlook_auto
                _send_via_outlook_auto('a@example.com', 'S', '<p>B</p>')
            mock_gc.assert_called_once()

    def test_dismiss_popup_called_before_keyboard_fallbacks(self, app):
        """_dismiss_outlook_security_popup is tried before keyboard fallbacks."""
        with app.app_context():
            mock_win32com, mock_outlook, mock_mail = self._make_win32_mocks()
            modules = {
                'win32com': mock_win32com,
                'win32com.client': mock_win32com.client,
                'win32api': MagicMock(),
                'win32con': MagicMock(),
            }
            with patch.dict('sys.modules', modules), \
                 patch('app.services.email_service._dismiss_outlook_security_popup', return_value=True) as mock_dismiss:
                from app.services.email_service import _send_via_outlook_auto
                result = _send_via_outlook_auto('a@example.com', 'S', '<p>B</p>')
            assert result is True
            mock_dismiss.assert_called_once()


class TestDismissOutlookSecurityPopup:
    """Tests for the win32gui-based popup dismissal helper."""

    def test_returns_false_when_win32gui_unavailable(self, app):
        """_dismiss_outlook_security_popup returns False when win32gui is not installed."""
        with app.app_context():
            # On non-Windows environments win32gui is not installed; importing it
            # raises ImportError, which the function catches and returns False.
            from app.services.email_service import _dismiss_outlook_security_popup
            result = _dismiss_outlook_security_popup()
            assert result is False

    def test_clicks_permitir_button_when_found(self, app):
        """_dismiss_outlook_security_popup clicks the 'Permitir' button and returns True."""
        with app.app_context():
            mock_win32gui = MagicMock()
            mock_win32con = MagicMock()
            mock_win32con.BM_CLICK = 0xF5

            # Simulate one visible window titled "Microsoft Outlook"
            mock_win32gui.IsWindowVisible.return_value = True
            mock_win32gui.GetWindowText.return_value = 'Microsoft Outlook'

            # Capture the child-enumeration callback so we can invoke it
            child_callbacks: list = []

            def capture_enum_child(hwnd, callback, extra):
                child_callbacks.append(callback)

            mock_win32gui.EnumChildWindows.side_effect = capture_enum_child

            def invoke_enum_windows(callback, extra):
                callback(1001, extra)  # call with a fake hwnd
                # Now trigger child enumeration with a fake "Permitir" button
                if child_callbacks:
                    mock_win32gui.GetClassName.return_value = 'Button'
                    mock_win32gui.GetWindowText.return_value = 'Permitir'
                    child_callbacks[0](2001, None)  # fake child hwnd

            mock_win32gui.EnumWindows.side_effect = invoke_enum_windows

            modules = {'win32gui': mock_win32gui, 'win32con': mock_win32con}
            with patch.dict('sys.modules', modules):
                from app.services.email_service import _dismiss_outlook_security_popup
                result = _dismiss_outlook_security_popup()

            assert result is True
            mock_win32gui.SendMessage.assert_called_once_with(2001, mock_win32con.BM_CLICK, 0, 0)

    def test_returns_false_when_no_outlook_window_found(self, app):
        """_dismiss_outlook_security_popup returns False when no matching window exists."""
        with app.app_context():
            mock_win32gui = MagicMock()
            mock_win32con = MagicMock()

            mock_win32gui.IsWindowVisible.return_value = True
            mock_win32gui.GetWindowText.return_value = 'Some Other App'
            mock_win32gui.EnumWindows.side_effect = lambda cb, extra: cb(1001, extra)

            modules = {'win32gui': mock_win32gui, 'win32con': mock_win32con}
            with patch.dict('sys.modules', modules):
                from app.services.email_service import _dismiss_outlook_security_popup
                result = _dismiss_outlook_security_popup()

            assert result is False
            mock_win32gui.EnumChildWindows.assert_not_called()


class TestSendViaSmtp:
    """Tests for the SMTP transport."""

    def test_returns_false_when_config_incomplete(self, app):
        """_send_via_smtp returns False when MAIL_* env vars are missing."""
        with app.app_context():
            with patch.dict('os.environ', {}, clear=True):
                # Remove any MAIL_ env vars
                import os
                for key in list(os.environ.keys()):
                    if key.startswith('MAIL_'):
                        del os.environ[key]
                from app.services.email_service import _send_via_smtp
                result = _send_via_smtp('to@example.com', 'Subject', '<p>Body</p>')
                assert result is False

    def test_returns_true_when_smtp_succeeds(self, app):
        """_send_via_smtp returns True when SMTP connection succeeds."""
        with app.app_context():
            env_vars = {
                'MAIL_SERVER': 'smtp.example.com',
                'MAIL_PORT': '587',
                'MAIL_USERNAME': 'user@example.com',
                'MAIL_PASSWORD': 'password',
                'MAIL_DEFAULT_SENDER': 'user@example.com',
            }
            with patch.dict('os.environ', env_vars):
                mock_server = MagicMock()
                with patch('smtplib.SMTP') as mock_smtp:
                    mock_smtp.return_value.__enter__ = lambda s: mock_server
                    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
                    from app.services.email_service import _send_via_smtp
                    result = _send_via_smtp('to@example.com', 'Subject', '<p>Body</p>')
                    assert result is True
                    mock_server.starttls.assert_called_once()
                    mock_server.login.assert_called_once_with('user@example.com', 'password')


class TestTokenHelpers:
    """Tests for generate_reset_token and validate_reset_token."""

    def test_generate_reset_token_creates_token(self, app, db):
        """generate_reset_token creates a valid PasswordResetToken."""
        from app.models.user import User
        from app.services.email_service import generate_reset_token

        with app.app_context():
            user = User(username='tokenuser', email='tokenuser@example.com')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

            token = generate_reset_token(user)
            assert token is not None
            assert token.token is not None
            assert token.user_id == user.id
            assert not token.used

            db.session.delete(user)
            db.session.commit()

    def test_validate_reset_token_returns_user_for_valid_token(self, app, db):
        """validate_reset_token returns the user for a valid token."""
        from app.models.user import User
        from app.services.email_service import generate_reset_token, validate_reset_token

        with app.app_context():
            user = User(username='validtoken', email='validtoken@example.com')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

            token = generate_reset_token(user)
            result_user, error = validate_reset_token(token.token)
            assert error is None
            assert result_user is not None
            assert result_user.id == user.id

            db.session.delete(user)
            db.session.commit()

    def test_validate_reset_token_returns_error_for_invalid_token(self, app, db):
        """validate_reset_token returns an error message for a non-existent token."""
        from app.services.email_service import validate_reset_token

        with app.app_context():
            result_user, error = validate_reset_token('nonexistent-token-string')
            assert result_user is None
            assert error is not None


class TestHighLevelHelpers:
    """Tests for send_user_registration_email, send_admin_registration_notification, send_password_reset_email."""

    def _make_user(self, username='helpuser', email='helpuser@example.com', role='engineer'):
        user = MagicMock()
        user.username = username
        user.email = email
        user.full_name = 'Help User'
        user.role = role
        return user

    def test_send_user_registration_email_calls_send_email(self, app):
        """send_user_registration_email calls send_email with the reset_link."""
        with app.app_context():
            user = self._make_user()
            with patch('app.services.email_service.send_email', return_value=True) as mock_send:
                from app.services.email_service import send_user_registration_email
                result = send_user_registration_email(user, 'http://example.com/reset/abc')
                assert result is True
                mock_send.assert_called_once()
                args = mock_send.call_args[0]
                assert args[0] == user.email
                assert 'http://example.com/reset/abc' in args[2]

    def test_send_admin_registration_notification_calls_send_email(self, app):
        """send_admin_registration_notification calls send_email with admin's address."""
        with app.app_context():
            admin = self._make_user('admin', 'admin@example.com', 'admin')
            new_user = self._make_user()
            with patch('app.services.email_service.send_email', return_value=True) as mock_send:
                from app.services.email_service import send_admin_registration_notification
                result = send_admin_registration_notification(admin, new_user)
                assert result is True
                mock_send.assert_called_once()
                assert mock_send.call_args[0][0] == admin.email

    def test_send_password_reset_email_calls_send_email(self, app):
        """send_password_reset_email calls send_email with the reset_link."""
        with app.app_context():
            user = self._make_user()
            with patch('app.services.email_service.send_email', return_value=True) as mock_send:
                from app.services.email_service import send_password_reset_email
                result = send_password_reset_email(user, 'http://example.com/reset/xyz')
                assert result is True
                mock_send.assert_called_once()
                args = mock_send.call_args[0]
                assert args[0] == user.email
                assert 'http://example.com/reset/xyz' in args[2]
