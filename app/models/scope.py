"""Scope management models (PMBOK - Escopo)."""
from datetime import datetime
from app import db


class Requirement(db.Model):
    """Project requirement model."""

    __tablename__ = 'requirements'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    acceptance_criteria: str = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(32), default='draft')  # draft, active, validated, rejected
    priority: str = db.Column(db.String(16), default='medium')  # low, medium, high, critical
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Requirement {self.title}>'


class WBSItem(db.Model):
    """Work Breakdown Structure item model."""

    __tablename__ = 'wbs_items'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    parent_id: int = db.Column(db.Integer, db.ForeignKey('wbs_items.id'), nullable=True)
    code: str = db.Column(db.String(64), nullable=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    level: int = db.Column(db.Integer, default=1)
    status: str = db.Column(db.String(32), default='active')  # draft, active, closed
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential relationship for hierarchy
    children = db.relationship('WBSItem', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self) -> str:
        return f'<WBSItem {self.code} {self.title}>'


class ScopeChange(db.Model):
    """Scope change request model."""

    __tablename__ = 'scope_changes'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    reason: str = db.Column(db.Text, nullable=True)
    impact: str = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(32), default='pending')  # pending, approved, rejected, implemented
    requested_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at: datetime = db.Column(db.DateTime, nullable=True)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ScopeChange {self.title}>'
