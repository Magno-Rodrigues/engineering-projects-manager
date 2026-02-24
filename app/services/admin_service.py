<<<<<<< HEAD
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
=======
"""Admin service for user CRUD operations."""
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from app import db
from app.models.user import User

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for admin user management operations."""

    @staticmethod
    def list_users(key_filter: str = '', name_filter: str = '') -> List[User]:
        """Return all users, optionally filtered by key or name.

        Args:
            key_filter: Filter by user key (partial match).
            name_filter: Filter by full name or username (partial match).
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

        Returns:
            List of matching User objects.
        """
        query = User.query
<<<<<<< HEAD
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
=======
        if key_filter:
            query = query.filter(User.key.ilike(f'%{key_filter}%'))
        if name_filter:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f'%{name_filter}%'),
                    User.username.ilike(f'%{name_filter}%'),
                )
            )
        return query.order_by(User.full_name).all()

    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        return db.session.get(User, user_id)

    @staticmethod
    def create_user(data: Dict, admin_id: Optional[int] = None) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user.

        Args:
            data: Dictionary of user fields.
            admin_id: ID of the admin performing the action.

        Returns:
            Tuple of (User, None) on success or (None, error_message) on failure.
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
        """
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
<<<<<<< HEAD
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
=======
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'engineer')
        key = data.get('key', '').strip() or None

        if not username:
            return None, 'Nome de usuário é obrigatório.'
        if not email:
            return None, 'E-mail é obrigatório.'
        if not password:
            return None, 'Senha é obrigatória.'
        if User.query.filter_by(username=username).first():
            return None, 'Nome de usuário já está em uso.'
        if User.query.filter_by(email=email).first():
            return None, 'E-mail já está cadastrado.'
        if key and User.query.filter_by(key=key).first():
            return None, 'Chave já está em uso.'

        user = User(
            username=username,
            email=email,
            full_name=full_name or None,
            role=role,
            key=key,
            phone=data.get('phone') or None,
            supervision=data.get('supervision') or None,
            function=data.get('function') or None,
            company=data.get('company') or None,
            state=data.get('state') or None,
            measurement_criteria=data.get('measurement_criteria') or None,
            birth_date=AdminService._parse_date(data.get('birth_date')),
            start_appointment_date=AdminService._parse_date(data.get('start_appointment_date')),
            status=data.get('status', 'Ativo'),
            password_reset_required=True,
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
<<<<<<< HEAD
        return user, None

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
=======
        if admin_id is not None:
            logger.info('Admin %s created user %s', admin_id, username)
        return user, None

    @staticmethod
    def update_user(user_id: int, data: Dict, admin_id: Optional[int] = None) -> Tuple[Optional[User], Optional[str]]:
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
        """Update an existing user.

        Args:
            user_id: ID of the user to update.
            data: Dictionary of fields to update.
<<<<<<< HEAD

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
=======
            admin_id: ID of the admin performing the action.

        Returns:
            Tuple of (User, None) on success or (None, error_message) on failure.
        """
        user = db.session.get(User, user_id)
        if not user:
            return None, 'Usuário não encontrado.'

        email = data.get('email', '').strip()
        key = data.get('key', '').strip() or None

        if email and email != user.email:
            if User.query.filter(User.email == email, User.id != user_id).first():
                return None, 'E-mail já está cadastrado.'
            user.email = email

        if key and key != user.key:
            if User.query.filter(User.key == key, User.id != user_id).first():
                return None, 'Chave já está em uso.'

        user.full_name = data.get('full_name') or user.full_name
        user.role = data.get('role', user.role)
        user.key = key if key is not None else user.key
        user.phone = data.get('phone') if data.get('phone') is not None else user.phone
        user.supervision = data.get('supervision') if data.get('supervision') is not None else user.supervision
        user.function = data.get('function') if data.get('function') is not None else user.function
        user.company = data.get('company') if data.get('company') is not None else user.company
        user.state = data.get('state') if data.get('state') is not None else user.state
        user.measurement_criteria = data.get('measurement_criteria') if data.get('measurement_criteria') is not None else user.measurement_criteria
        user.status = data.get('status', user.status)

        if data.get('birth_date'):
            user.birth_date = AdminService._parse_date(data['birth_date'])
        if data.get('start_appointment_date'):
            user.start_appointment_date = AdminService._parse_date(data['start_appointment_date'])

        password = data.get('password', '').strip()
        if password:
            user.set_password(password)
            user.password_reset_required = True
            user.first_login = True

        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s updated user %s', admin_id, user.username)
        return user, None

    @staticmethod
    def delete_user(user_id: int, admin_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
        """Delete a user by ID.

        Args:
            user_id: ID of the user to delete.
<<<<<<< HEAD

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
=======
            admin_id: ID of the admin performing the action.

        Returns:
            Tuple of (True, None) on success or (False, error_message) on failure.
        """
        user = db.session.get(User, user_id)
        if not user:
            return False, 'Usuário não encontrado.'
        username = user.username
        db.session.delete(user)
        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s deleted user %s', admin_id, username)
        return True, None

    @staticmethod
    def update_permissions(user_id: int, permissions: Dict, admin_id: Optional[int] = None) -> Tuple[Optional[User], Optional[str]]:
        """Update the JSON permissions for a user.

        Args:
            user_id: ID of the user.
            permissions: Dictionary of permission flags.
            admin_id: ID of the admin performing the action.

        Returns:
            Tuple of (User, None) on success or (None, error_message) on failure.
        """
        user = db.session.get(User, user_id)
        if not user:
            return None, 'Usuário não encontrado.'
        user.permissions = permissions
        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s updated permissions for user %s', admin_id, user.username)
        return user, None

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        """Parse a date string in dd/mm/yyyy or yyyy-mm-dd format."""
        from datetime import datetime as _dt
        if not value:
            return None
        value = value.strip()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return _dt.strptime(value, fmt).date()
            except ValueError:
                continue
        return None
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
