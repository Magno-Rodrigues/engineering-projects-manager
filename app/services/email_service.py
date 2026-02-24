"""Email service for sending password reset and welcome emails.

Hybrid email backend:
- Development on Windows: uses Outlook COM (win32com) with automated
  permission-popup handling - no manual interaction required.
- Production / Linux / any other environment: uses SMTP via smtplib with the
  MAIL_* environment variables.
"""
import gc
import logging
import os
import platform
import secrets
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

from flask import url_for

from app import db
from app.models.reset_token import PasswordResetToken

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 12


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def generate_reset_token(user) -> PasswordResetToken:
    """Generate a password-reset token for *user* valid for TOKEN_EXPIRY_HOURS.

    Any previously unused token for the user is invalidated first.

    Args:
        user: The User instance for which the token is generated.

    Returns:
        The newly created :class:`PasswordResetToken` instance.
    """
    # Invalidate existing unused tokens for this user
    PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
    db.session.flush()

    token_str = secrets.token_urlsafe(48)
    token = PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
    )
    db.session.add(token)
    db.session.commit()
    return token


def validate_reset_token(token_str: str) -> Tuple[Optional[object], Optional[str]]:
    """Validate a password-reset token string.

    Args:
        token_str: The raw token string from the URL.

    Returns:
        Tuple of (User, None) if valid, or (None, error_message) if invalid.
    """
    from app.models.user import User  # avoid circular import at module level

    token = PasswordResetToken.query.filter_by(token=token_str).first()
    if not token:
        return None, 'Link de redefinição inválido.'
    if not token.is_valid():
        return None, 'Este link expirou ou já foi utilizado.'
    user = db.session.get(User, token.user_id)
    if not user:
        return None, 'Usuário não encontrado.'
    return user, None


# ---------------------------------------------------------------------------
# Low-level transport
# ---------------------------------------------------------------------------

def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """Send an e-mail, automatically choosing the transport method.

    - Windows + development environment -> Outlook COM with automated popup handling
    - All other cases (production, Linux, macOS, ...) -> SMTP

    Args:
        to_email: Recipient e-mail address.
        subject: E-mail subject line.
        body_html: HTML body of the e-mail.

    Returns:
        True if the e-mail was sent successfully, False otherwise.
    """
    try:
        from flask import current_app
        env = current_app.config.get('ENV', 'development')
    except RuntimeError:
        env = os.getenv('ENV', 'development')

    system = platform.system()

    if env == 'development' and system == 'Windows':
        return _send_via_outlook_auto(to_email, subject, body_html)

    return _send_via_smtp(to_email, subject, body_html)


def _dismiss_outlook_security_popup() -> bool:
    """Find and click the 'Permitir'/'Allow' button in the Outlook security popup.

    Uses ``win32gui`` to enumerate all visible top-level windows, looking for
    an Outlook security dialog.  When found, its child Button controls are
    inspected and the first one labelled 'Permitir' or 'Allow' is clicked
    directly via ``BM_CLICK`` -- no keyboard focus required.

    Returns:
        True if the button was found and clicked, False otherwise.
    """
    try:
        import win32gui  # type: ignore[import]
        import win32con  # type: ignore[import]

        clicked: list[bool] = []

        def _check_child(child_hwnd: int, _: object) -> None:
            if clicked:
                return  # already clicked
            class_name = win32gui.GetClassName(child_hwnd)
            text = win32gui.GetWindowText(child_hwnd)
            if class_name == 'Button' and text.strip() in ('Permitir', 'Allow'):
                win32gui.SendMessage(child_hwnd, win32con.BM_CLICK, 0, 0)
                clicked.append(True)

        def _check_window(hwnd: int, _: object) -> None:
            if clicked or not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if 'Outlook' in title or 'Microsoft' in title:
                try:
                    win32gui.EnumChildWindows(hwnd, _check_child, None)
                except Exception:  # noqa: BLE001
                    pass

        win32gui.EnumWindows(_check_window, None)
        return bool(clicked)
    except Exception:  # noqa: BLE001
        return False


def _send_via_outlook_auto(to_email: str, subject: str, body_html: str) -> bool:
    """Send e-mail via Outlook COM with automated permission-popup handling.

    Falls back to SMTP on any error.

    Args:
        to_email: Recipient e-mail address.
        subject: E-mail subject line.
        body_html: HTML body of the e-mail.

    Returns:
        True on success, False on failure (including SMTP fallback failure).
    """
    outlook = None
    mail = None
    try:
        import win32com.client  # type: ignore[import]
        import win32api  # type: ignore[import]
        import win32con  # type: ignore[import]

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = MailItem

        mail.To = to_email
        mail.Subject = subject
        mail.HTMLBody = body_html
        if outlook.Session.Accounts.Count > 0:
            mail.SendUsingAccount = outlook.Session.Accounts.Item(1)

        mail.Send()

        # Wait briefly for any permission popup to appear, then dismiss it.
        time.sleep(0.5)

        # Technique 1: direct button click via win32gui (focus-independent)
        if not _dismiss_outlook_security_popup():
            # Technique 2: pyautogui TAB + ENTER
            try:
                import pyautogui  # type: ignore[import]
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.press('return')
            except Exception:  # noqa: BLE001
                # Technique 3: win32api low-level keyboard events
                try:
                    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                except Exception:  # noqa: BLE001
                    pass  # Email was already sent; popup automation is best-effort

        logger.info('[Outlook COM] Email enviado para %s', to_email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('[Outlook COM] Erro ao enviar para %s: %s - tentando SMTP como fallback', to_email, exc)
        return _send_via_smtp(to_email, subject, body_html)
    finally:
        # Release COM objects so subsequent sends get a fresh connection
        mail = None
        outlook = None
        gc.collect()


def _send_via_smtp(to_email: str, subject: str, body_html: str) -> bool:
    """Send e-mail via SMTP using environment variables for configuration.

    Required environment variables: MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER.  MAIL_PORT defaults to 587.

    Args:
        to_email: Recipient e-mail address.
        subject: E-mail subject line.
        body_html: HTML body of the e-mail.

    Returns:
        True on success, False on failure.
    """
    try:
        mail_server = os.getenv('MAIL_SERVER')
        mail_port = int(os.getenv('MAIL_PORT', 587))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_username)

        if not all([mail_server, mail_username, mail_password, mail_sender]):
            logger.warning('[SMTP] Configuração incompleta nas variáveis de ambiente')
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_sender
        msg['To'] = to_email
        msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)

        logger.info('[SMTP] Email enviado para %s', to_email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('[SMTP] Erro ao enviar para %s: %s', to_email, exc)
        return False


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------

def send_user_registration_email(user, reset_link: str) -> bool:
    """Send a welcome e-mail with a password-reset link to a newly registered *user*.

    Args:
        user: The User instance to send the email to.
        reset_link: The full URL the user should visit to set their password.

    Returns:
        True if the email was sent, False otherwise.
    """
    display_name = user.full_name or user.username
    subject = 'Bem-vindo ao Sistema de Gerenciamento!'
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #0066cc;">Bem-vindo, {display_name}!</h2>
                <p>Você foi cadastrado com sucesso no <strong>Sistema de Gerenciamento de Projetos de Engenharia</strong>.</p>
                <p>Para acessar o sistema e definir sua senha, clique no botão abaixo:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Acessar Sistema
                    </a>
                </div>
                <p style="color: #666; font-size: 12px;">
                    <strong>Atenção:</strong> Este link expira em <strong>12 horas</strong>.
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Se você não solicitou este cadastro, ignore este email.<br>
                    © 2026 Sistema RGM. Todos os direitos reservados.
                </p>
            </div>
        </body>
    </html>
    """
    result = send_email(user.email, subject, body_html)
    if result:
        logger.info('Registration email sent to %s', user.email)
    else:
        logger.warning('Failed to send registration email to %s', user.email)
    return result


# Backward-compatible alias
send_welcome_email = send_user_registration_email


def send_admin_registration_notification(admin, user) -> bool:
    """Send a confirmation e-mail to *admin* when a new user is registered.

    Args:
        admin: The admin User instance to notify.
        user: The newly created User instance.

    Returns:
        True if the email was sent, False otherwise.
    """
    admin_name = admin.full_name or admin.username
    user_name = user.full_name or user.username
    role_label = 'Administrador' if user.role == 'admin' else 'Usuário'
    subject = 'Novo Usuário Cadastrado'
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #0066cc;">Novo Usuário Cadastrado</h2>
                <p>Olá {admin_name},</p>
                <p>Um novo usuário foi cadastrado com sucesso:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Nome:</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{user_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Email:</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{user.email}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Tipo:</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{role_label}</td>
                    </tr>
                </table>
                <p>O usuário receberá um email com instruções de acesso.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    © 2026 Sistema RGM. Todos os direitos reservados.
                </p>
            </div>
        </body>
    </html>
    """
    result = send_email(admin.email, subject, body_html)
    if result:
        logger.info('Admin registration notification sent to %s', admin.email)
    else:
        logger.warning('Failed to send admin notification to %s', admin.email)
    return result


def send_password_reset_email(user, reset_link: str) -> bool:
    """Send an e-mail to *user* notifying that their password was changed by an admin.

    Args:
        user: The User instance whose password was reset.
        reset_link: The full URL the user should visit to set a new password.

    Returns:
        True if the email was sent, False otherwise.
    """
    display_name = user.full_name or user.username
    subject = 'Sua Senha foi Alterada'
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #0066cc;">Alteração de Senha</h2>
                <p>Olá {display_name},</p>
                <p>Sua senha foi alterada pelo administrador do sistema.</p>
                <p>Para redefinir sua senha, clique no botão abaixo:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Redefinir Senha
                    </a>
                </div>
                <p style="color: #666; font-size: 12px;">
                    <strong>Atenção:</strong> Este link expira em <strong>12 horas</strong>.
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Se você não solicitou esta alteração, entre em contato com o administrador.<br>
                    © 2026 Sistema RGM. Todos os direitos reservados.
                </p>
            </div>
        </body>
    </html>
    """
    result = send_email(user.email, subject, body_html)
    if result:
        logger.info('Password reset email sent to %s', user.email)
    else:
        logger.warning('Failed to send password reset email to %s', user.email)
    return result
