"""Email service for sending application emails."""
import logging
from flask import render_template, current_app
from flask_mail import Message

from app import mail

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for email operations."""

    @staticmethod
    def send_welcome_email(user_email: str, user_name: str, reset_token: str) -> bool:
        """Send a welcome email with a password reset link to a new user.

        Args:
            user_email: Recipient email address.
            user_name: Recipient display name.
            reset_token: Password reset token for the user.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        try:
            reset_url = f'{current_app.config.get("APP_BASE_URL", "http://localhost:5000")}/reset-password?token={reset_token}'
            msg = Message(
                subject='Bem-vindo ao Engineering Projects Manager',
                recipients=[user_email],
            )
            msg.html = render_template(
                'emails/welcome.html',
                user_name=user_name,
                user_email=user_email,
                reset_url=reset_url,
            )
            mail.send(msg)
            logger.info('Welcome email sent to %s', user_email)
            return True
        except Exception as exc:
            logger.error('Failed to send welcome email to %s: %s', user_email, exc)
            return False
