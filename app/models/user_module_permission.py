"""UserModulePermission model."""
from datetime import datetime, timezone
from app import db


class UserModulePermission(db.Model):
    """Maps CRUD permissions for a user on a specific module."""

    __tablename__ = 'user_module_permissions'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_name: str = db.Column(db.String(64), nullable=False)
    can_create: bool = db.Column(db.Boolean, default=False)
    can_read: bool = db.Column(db.Boolean, default=False)
    can_update: bool = db.Column(db.Boolean, default=False)
    can_delete: bool = db.Column(db.Boolean, default=False)
    granted_by_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    granted_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='module_permissions')
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_name', name='uq_user_module'),
    )

    def __repr__(self) -> str:
        return f'<UserModulePermission user={self.user_id} module={self.module_name}>'
