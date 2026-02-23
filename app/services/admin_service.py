"""Admin service for user CRUD operations."""
import json
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

        Returns:
            List of matching User objects.
        """
        query = User.query
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
        """
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
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
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s created user %s', admin_id, username)
        return user, None

    @staticmethod
    def update_user(user_id: int, data: Dict, admin_id: Optional[int] = None) -> Tuple[Optional[User], Optional[str]]:
        """Update an existing user.

        Args:
            user_id: ID of the user to update.
            data: Dictionary of fields to update.
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

        user.full_name = data.get('full_name', user.full_name) or user.full_name
        user.role = data.get('role', user.role)
        user.key = key if key is not None else user.key
        user.phone = data.get('phone') or user.phone
        user.supervision = data.get('supervision') or user.supervision
        user.function = data.get('function') or user.function
        user.company = data.get('company') or user.company
        user.state = data.get('state') or user.state
        user.measurement_criteria = data.get('measurement_criteria') or user.measurement_criteria
        user.status = data.get('status', user.status)

        if data.get('birth_date'):
            user.birth_date = AdminService._parse_date(data['birth_date'])
        if data.get('start_appointment_date'):
            user.start_appointment_date = AdminService._parse_date(data['start_appointment_date'])

        password = data.get('password', '').strip()
        if password:
            user.set_password(password)

        db.session.commit()
        if admin_id is not None:
            logger.info('Admin %s updated user %s', admin_id, user.username)
        return user, None

    @staticmethod
    def delete_user(user_id: int, admin_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Delete a user by ID.

        Args:
            user_id: ID of the user to delete.
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
