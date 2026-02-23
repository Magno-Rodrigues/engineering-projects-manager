"""Token service for generating and validating password reset tokens."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app import db
from app.models.user import User

TOKEN_EXPIRY_HOURS = 12


class TokenService:
    """Service class for password reset token operations."""

    @staticmethod
    def generate_reset_token(user: User) -> str:
        """Generate a secure password reset token for the given user.

        The token is stored on the user record with a 12-hour expiration.

        Args:
            user: The user to generate a token for.

        Returns:
            The generated URL-safe token string.
        """
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        db.session.commit()
        return token

    @staticmethod
    def verify_reset_token(token: str) -> Tuple[Optional[User], Optional[str]]:
        """Verify a password reset token and return the associated user.

        Args:
            token: The token string to verify.

        Returns:
            Tuple of (User, None) if valid, or (None, error_message) if invalid/expired.
        """
        if not token:
            return None, 'Token inválido.'
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return None, 'Token inválido ou já utilizado.'
        if user.reset_token_expires_at is None or datetime.utcnow() > user.reset_token_expires_at:
            return None, 'Token expirado. Solicite um novo link.'
        return user, None

    @staticmethod
    def invalidate_reset_token(user: User) -> None:
        """Invalidate the password reset token for the given user.

        Args:
            user: The user whose token should be cleared.
        """
        user.reset_token = None
        user.reset_token_expires_at = None
        db.session.commit()
