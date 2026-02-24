"""Utility for seeding default ModulePermission records in the database."""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Default modules to register on first run
DEFAULT_MODULES: List[Dict[str, str]] = [
    {
        'module_name': 'projects',
        'display_name': 'Projetos',
        'description': 'Gerenciamento de projetos de engenharia',
        'icon': 'folder',
    },
    {
        'module_name': 'tasks',
        'display_name': 'Tarefas',
        'description': 'Gerenciamento de tarefas de projetos',
        'icon': 'check-square',
    },
    {
        'module_name': 'reports',
        'display_name': 'Relatórios',
        'description': 'Geração e visualização de relatórios',
        'icon': 'file-text',
    },
]


def initialize_modules() -> None:
    """Seed the database with default ModulePermission records.

    Inserts any module from DEFAULT_MODULES that does not yet exist.
    Already-existing modules are left unchanged so that manual edits
    (e.g. custom display names) are preserved.

    This function must be called inside an active application context.
    """
    from app import db
    from app.models.module_permission import ModulePermission

    try:
        for module_data in DEFAULT_MODULES:
            existing = ModulePermission.query.filter_by(
                module_name=module_data['module_name']
            ).first()
            if existing is None:
                module = ModulePermission(
                    module_name=module_data['module_name'],
                    display_name=module_data['display_name'],
                    description=module_data['description'],
                    icon=module_data['icon'],
                    is_active=True,
                )
                db.session.add(module)
                logger.info("Registered module '%s'.", module_data['module_name'])
            else:
                logger.debug("Module '%s' already exists, skipping.", module_data['module_name'])
        db.session.commit()
        logger.info('Module initialization complete.')
    except Exception:
        db.session.rollback()
        logger.exception('Failed to initialize modules.')
        raise


def init_default_modules() -> None:
    """Backward-compatible alias for module initialization."""
    initialize_modules()
