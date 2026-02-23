"""Admin service for user management operations."""
from typing import Any, Dict, List, Optional, Tuple
from app import db
from app.models.user import User


class AdminService:
    """Service class for administrative user management."""

    @staticmethod
    def list_all_users(search_key: str = '', search_name: str = '') -> List[User]:
        """Return all users, optionally filtered by username key or full name.

        Args:
            search_key: Filter by username (partial match).
            search_name: Filter by full name (partial match).

        Returns:
            List of matching User objects.
        """
        query = User.query
        if search_key:
            query = query.filter(User.username.ilike(f'%{search_key}%'))
        if search_name:
            query = query.filter(User.full_name.ilike(f'%{search_name}%'))
        return query.order_by(User.id).all()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Return a user by primary key.

        Args:
            user_id: The user's ID.

        Returns:
            The User object, or None if not found.
        """
        return User.query.get(user_id)

    @staticmethod
    def create_user(data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user from a data dictionary.

        Args:
            data: Dictionary containing user fields.

        Returns:
            A tuple of (User, None) on success or (None, error_message) on failure.
        """
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        if not username:
            return None, 'Username is required.'
        if not email:
            return None, 'Email is required.'
        if not password:
            return None, 'Password is required.'
        if User.query.filter_by(username=username).first():
            return None, 'Username already taken.'
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered.'
        user = User(
            username=username,
            email=email,
            full_name=data.get('full_name', '').strip() or None,
            role=data.get('role', 'engineer'),
            is_active=data.get('is_active', True),
            phone=data.get('phone', '').strip() or None,
            job_title=data.get('job_title', '').strip() or None,
            company=data.get('company', '').strip() or None,
            supervisor=data.get('supervisor', '').strip() or None,
            birth_date=data.get('birth_date') or None,
            appointment_start_date=data.get('appointment_start_date') or None,
            measurement_criterion=data.get('measurement_criterion', '').strip() or None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user, None

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """Update an existing user.

        Args:
            user_id: ID of the user to update.
            data: Dictionary of fields to update.

        Returns:
            A tuple of (User, None) on success or (None, error_message) on failure.
        """
        user = User.query.get(user_id)
        if not user:
            return None, 'User not found.'

        new_username = data.get('username', '').strip()
        new_email = data.get('email', '').strip()
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return None, 'Username already taken.'
            user.username = new_username
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                return None, 'Email already registered.'
            user.email = new_email

        if data.get('password', '').strip():
            user.set_password(data['password'].strip())

        updatable = ('full_name', 'role', 'phone', 'job_title', 'company',
                     'supervisor', 'birth_date', 'appointment_start_date',
                     'measurement_criterion')
        for field in updatable:
            if field in data:
                setattr(user, field, data[field] or None)

        if 'is_active' in data:
            user.is_active = bool(data['is_active'])

        db.session.commit()
        return user, None

    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a user by ID.

        Args:
            user_id: ID of the user to delete.

        Returns:
            A tuple of (True, None) on success or (False, error_message) on failure.
        """
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found.'
        db.session.delete(user)
        db.session.commit()
        return True, None

    @staticmethod
    def delete_multiple_users(user_ids: List[int]) -> Tuple[int, List[int]]:
        """Delete multiple users by their IDs.

        Args:
            user_ids: List of user IDs to delete.

        Returns:
            A tuple of (deleted_count, not_found_ids).
        """
        deleted = 0
        not_found = []
        for uid in user_ids:
            user = User.query.get(uid)
            if user:
                db.session.delete(user)
                deleted += 1
            else:
                not_found.append(uid)
        db.session.commit()
        return deleted, not_found
