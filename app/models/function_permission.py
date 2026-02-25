"""FunctionPermission model."""
from datetime import datetime
from app import db


class FunctionPermission(db.Model):
    """Represents a granular function-level permission for a user within a module."""

    __tablename__ = 'function_permissions'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_name: str = db.Column(db.String(64), nullable=False)
    function_name: str = db.Column(db.String(64), nullable=False)
    has_permission: bool = db.Column(db.Boolean, default=False, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='function_permissions')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_name', 'function_name', name='uq_user_module_function'),
    )

    def __repr__(self) -> str:
        return f'<FunctionPermission user={self.user_id} {self.module_name}.{self.function_name}={self.has_permission}>'
