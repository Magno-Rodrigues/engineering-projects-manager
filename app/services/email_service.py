"""Email service for sending password reset and welcome emails.

Sends via Outlook COM (MAPI) when running on Windows with Outlook installed,
falling back to Flask-Mail when Outlook is unavailable.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from flask import current_app, url_for

from app import db
from app.models.reset_token import PasswordResetToken

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 12


def send_email_via_outlook(to_email: str, subject: str, body_html: str) -> bool:
    """Send an email using the locally installed Outlook application (MAPI/COM).

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body_html: HTML body content.

    Returns:
        True if the email was dispatched successfully, False otherwise.
    """
    try:
        import win32com.client  # type: ignore[import]

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = MailItem
        mail.To = to_email
        mail.Subject = subject
        mail.HTMLBody = body_html
        mail.Send()
        logger.info("✅ Email enviado para %s via Outlook COM", to_email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("❌ Erro ao enviar email via Outlook COM para %s: %s", to_email, exc)
        return False


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


def send_user_registration_email(user, token: PasswordResetToken) -> bool:
    """Send a welcome e-mail with a password-reset link to a newly registered *user*.

    Uses Outlook COM (MAPI) when available; falls back to Flask-Mail otherwise.

    Args:
        user: The User instance to send the email to.
        token: The PasswordResetToken to embed in the link.

    Returns:
        True if the email was sent, False otherwise.
    """
    reset_url = url_for('auth.reset_password', token=token.token, _external=True)
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
                    <a href="{reset_url}" style="background-color: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
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

    if send_email_via_outlook(user.email, subject, body_html):
        return True

    # Fallback: Flask-Mail
    try:
        from flask_mail import Message
        from app import mail  # imported lazily so tests without Flask-Mail still work

        body = (
            f'Olá {display_name},\n\n'
            'Parabéns! Você foi cadastrado no Sistema de Gerenciamento de Projetos de Engenharia.\n\n'
            'Para acessar o sistema e definir sua senha, clique no link abaixo:\n'
            f'{reset_url}\n\n'
            'Este link expira em 12 horas.\n\n'
            'Atenciosamente,\n'
            'Sistema RGM'
        )
        msg = Message(subject=subject, recipients=[user.email], body=body, html=body_html)
        mail.send(msg)
        logger.info('Registration email sent to %s via Flask-Mail', user.email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('Failed to send registration email to %s: %s', user.email, exc)
        return False


# Backward-compatible alias
send_welcome_email = send_user_registration_email


def send_admin_registration_notification(admin, user) -> bool:
    """Send a confirmation e-mail to *admin* when a new user is registered.

    Uses Outlook COM (MAPI) when available; falls back to Flask-Mail otherwise.

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

    if send_email_via_outlook(admin.email, subject, body_html):
        return True

    # Fallback: Flask-Mail
    try:
        from flask_mail import Message
        from app import mail

        body = (
            f'Olá {admin_name},\n\n'
            'Um novo usuário foi cadastrado com sucesso:\n\n'
            f'Nome: {user_name}\n'
            f'Email: {user.email}\n'
            f'Tipo: {role_label}\n\n'
            'O usuário receberá um email com instruções de acesso.\n\n'
            'Atenciosamente,\n'
            'Sistema RGM'
        )
        msg = Message(subject=subject, recipients=[admin.email], body=body, html=body_html)
        mail.send(msg)
        logger.info('Admin registration notification sent to %s via Flask-Mail', admin.email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('Failed to send admin notification to %s: %s', admin.email, exc)
        return False


def send_password_reset_email(user, token: PasswordResetToken) -> bool:
    """Send an e-mail to *user* notifying that their password was changed by an admin.

    Uses Outlook COM (MAPI) when available; falls back to Flask-Mail otherwise.

    Args:
        user: The User instance whose password was reset.
        token: The PasswordResetToken to embed in the link.

    Returns:
        True if the email was sent, False otherwise.
    """
    reset_url = url_for('auth.reset_password', token=token.token, _external=True)
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
                    <a href="{reset_url}" style="background-color: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
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

    if send_email_via_outlook(user.email, subject, body_html):
        return True

    # Fallback: Flask-Mail
    try:
        from flask_mail import Message
        from app import mail

        body = (
            f'Olá {display_name},\n\n'
            'Sua senha foi alterada pelo administrador.\n\n'
            'Para redefinir sua senha, clique no link abaixo:\n'
            f'{reset_url}\n\n'
            'Este link expira em 12 horas.\n\n'
            'Atenciosamente,\n'
            'Sistema RGM'
        )
        msg = Message(subject=subject, recipients=[user.email], body=body, html=body_html)
        mail.send(msg)
        logger.info('Password reset email sent to %s via Flask-Mail', user.email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('Failed to send password reset email to %s: %s', user.email, exc)
        return False
