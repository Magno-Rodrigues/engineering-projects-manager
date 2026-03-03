"""ModulePermission model."""
from datetime import datetime, timezone
from app import db


class ModulePermission(db.Model):
    """Represents a functional module available in the system."""

    __tablename__ = 'module_permissions'

    id: int = db.Column(db.Integer, primary_key=True)
    module_name: str = db.Column(db.String(64), unique=True, nullable=False)
    display_name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text)
    icon: str = db.Column(db.String(64))
    is_active: bool = db.Column(db.Boolean, default=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f'<ModulePermission {self.module_name}>'
