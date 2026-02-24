"""Initialize default modules in the database."""
import logging
from app import db
from app.models.module_permission import ModulePermission

logger = logging.getLogger(__name__)


def init_default_modules():
    """Initialize default modules if they don't exist."""
    modules = [
        {
            'module_name': 'projects',
            'display_name': 'Projetos',
            'description': 'Gerenciamento de projetos de engenharia',
            'icon': 'folder',
            'is_active': True,
        },
    ]
    
    for module_data in modules:
        # Verifica se já existe
        existing = ModulePermission.query.filter_by(
            module_name=module_data['module_name']
        ).first()
        
        if not existing:
            try:
                module = ModulePermission(**module_data)
                db.session.add(module)
                db.session.commit()
                logger.info(f"Module '{module_data['display_name']}' initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing module '{module_data['module_name']}': {str(e)}")
                db.session.rollback()
        else:
            logger.debug(f"Module '{module_data['module_name']}' already exists.")