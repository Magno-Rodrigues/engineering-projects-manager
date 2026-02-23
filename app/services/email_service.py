"""Email service for sending password reset and welcome emails."""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from flask import current_app, url_for

from app import db
from app.models.reset_token import PasswordResetToken

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 12


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


def send_welcome_email(user, token: PasswordResetToken) -> bool:
    """Send a welcome e-mail with a password-reset link to *user*.

    Uses Flask-Mail when it is configured; logs a warning and returns False
    when mail is not configured so that the rest of the application still works.

    Args:
        user: The User instance to send the email to.
        token: The PasswordResetToken to embed in the link.

    Returns:
        True if the email was sent, False otherwise.
    """
    try:
        from flask_mail import Message
        from app import mail  # imported lazily so tests without Flask-Mail still work

        reset_url = url_for(
            'auth.reset_password', token=token.token, _external=True
        )
        display_name = user.full_name or user.username
        subject = 'Bem-vindo ao Sistema de Gerenciamento de Projetos!'
        body = (
            f'Olá {display_name},\n\n'
            'Você foi cadastrado no Sistema de Gerenciamento de Projetos de Engenharia.\n\n'
            'Para acessar o sistema e definir sua senha, clique no link abaixo:\n'
            f'{reset_url}\n\n'
            'Este link expira em 12 horas.\n\n'
            'Se você não solicitou este cadastro, ignore este email.\n\n'
            'Atenciosamente,\n'
            'Sistema RGM'
        )
        msg = Message(subject=subject, recipients=[user.email], body=body)
        mail.send(msg)
        logger.info('Welcome email sent to %s', user.email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('Failed to send welcome email to %s: %s', user.email, exc)
        return False
