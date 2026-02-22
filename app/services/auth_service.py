"""Authentication service."""
from typing import Optional, Tuple
from app import db
from app.models.user import User


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password.

        Args:
            username: The username to authenticate.
            password: The plain-text password to verify.

        Returns:
            The authenticated User, or None if authentication fails.
        """
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def register(username: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user.

        Args:
            username: Desired username.
            email: User email address.
            password: Plain-text password.

        Returns:
            A tuple of (User, None) on success or (None, error_message) on failure.
        """
        if User.query.filter_by(username=username).first():
            return None, 'Username already taken.'
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered.'
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user, None
