"""Permission service for module-based access control."""
import logging
from typing import List, Optional, Tuple

from app import db
from app.models.module_permission import ModulePermission
from app.models.user_module_permission import UserModulePermission

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing module-based permissions."""

    @staticmethod
    def has_module_access(user_id: int, module_name: str) -> bool:
        """Check if a user has any access to a module.

        Args:
            user_id: The user's ID.
            module_name: The module identifier (e.g., 'projects').

        Returns:
            True if the user has at least one CRUD permission on the module.
        """
        perm = UserModulePermission.query.filter_by(
            user_id=user_id, module_name=module_name
        ).first()
        if not perm:
            return False
        return any([perm.can_create, perm.can_read, perm.can_update, perm.can_delete])

    @staticmethod
    def can_perform_action(user_id: int, module_name: str, action: str) -> bool:
        """Check if a user can perform a specific CRUD action on a module.

        Args:
            user_id: The user's ID.
            module_name: The module identifier.
            action: One of 'create', 'read', 'update', 'delete'.

        Returns:
            True if the user has the requested permission.
        """
        perm = UserModulePermission.query.filter_by(
            user_id=user_id, module_name=module_name
        ).first()
        if not perm:
            return False
        action_map = {
            'create': perm.can_create,
            'read': perm.can_read,
            'update': perm.can_update,
            'delete': perm.can_delete,
        }
        return bool(action_map.get(action, False))

    @staticmethod
    def grant_module_permission(
        user_id: int,
        module_name: str,
        can_create: bool = False,
        can_read: bool = False,
        can_update: bool = False,
        can_delete: bool = False,
        granted_by_id: Optional[int] = None,
    ) -> Tuple[Optional[UserModulePermission], Optional[str]]:
        """Grant or update module permissions for a user.

        Args:
            user_id: The user's ID.
            module_name: The module identifier.
            can_create: Grant create access.
            can_read: Grant read access.
            can_update: Grant update access.
            can_delete: Grant delete access.
            granted_by_id: ID of the admin granting the permission.

        Returns:
            Tuple of (UserModulePermission, None) on success or (None, error) on failure.
        """
        perm = UserModulePermission.query.filter_by(
            user_id=user_id, module_name=module_name
        ).first()
        if perm:
            perm.can_create = can_create
            perm.can_read = can_read
            perm.can_update = can_update
            perm.can_delete = can_delete
            perm.granted_by_id = granted_by_id
        else:
            perm = UserModulePermission(
                user_id=user_id,
                module_name=module_name,
                can_create=can_create,
                can_read=can_read,
                can_update=can_update,
                can_delete=can_delete,
                granted_by_id=granted_by_id,
            )
            db.session.add(perm)
        db.session.commit()
        logger.info('Permissions granted for user %s on module %s', user_id, module_name)
        return perm, None

    @staticmethod
    def revoke_module_permission(user_id: int, module_name: str) -> bool:
        """Revoke all permissions for a user on a module.

        Args:
            user_id: The user's ID.
            module_name: The module identifier.

        Returns:
            True if a permission record was deleted, False if none existed.
        """
        perm = UserModulePermission.query.filter_by(
            user_id=user_id, module_name=module_name
        ).first()
        if not perm:
            return False
        db.session.delete(perm)
        db.session.commit()
        logger.info('Permissions revoked for user %s on module %s', user_id, module_name)
        return True

    @staticmethod
    def get_user_modules(user_id: int) -> List[UserModulePermission]:
        """List all module permissions assigned to a user.

        Args:
            user_id: The user's ID.

        Returns:
            List of UserModulePermission objects.
        """
        return UserModulePermission.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_available_modules() -> List[ModulePermission]:
        """Return all active registered modules.

        Returns:
            List of active ModulePermission objects.
        """
        return ModulePermission.query.filter_by(is_active=True).order_by(ModulePermission.display_name).all()

    @staticmethod
    def get_user_permission(user_id: int, module_name: str) -> Optional[UserModulePermission]:
        """Get a user's permission record for a specific module.

        Args:
            user_id: The user's ID.
            module_name: The module identifier.

        Returns:
            UserModulePermission or None if not found.
        """
        return UserModulePermission.query.filter_by(
            user_id=user_id, module_name=module_name
        ).first()
