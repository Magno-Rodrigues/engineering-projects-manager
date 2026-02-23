"""Authentication service."""
import logging
import warnings
from typing import Optional, Tuple
from app import db
from app.models.user import User

logger = logging.getLogger(__name__)


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

        .. deprecated::
            Use :meth:`register_user_by_admin` instead.

        Args:
            username: Desired username.
            email: User email address.
            password: Plain-text password.

        Returns:
            A tuple of (User, None) on success or (None, error_message) on failure.
        """
        warnings.warn(
            'AuthService.register() is deprecated. Use register_user_by_admin() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return AuthService.register_user_by_admin(username, email, password)

    @staticmethod
    def register_user_by_admin(
        username: str,
        email: str,
        password: str,
        role: str = 'engineer',
        admin_id: Optional[int] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user on behalf of an admin.

        Args:
            username: Desired username.
            email: User email address.
            password: Plain-text password.
            role: Role assigned to the new user (default: 'engineer').
            admin_id: ID of the admin creating the user (for auditing).

        Returns:
            A tuple of (User, None) on success or (None, error_message) on failure.
        """
        if User.query.filter_by(username=username).first():
            return None, 'Username already taken.'
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered.'
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s created user %s with role %s', admin_id, username, role)
        return user, None
