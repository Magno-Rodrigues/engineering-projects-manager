"""ScopeChange model for PMBOK Scope Knowledge Area."""
from datetime import datetime, timezone, date
from app import db


class ScopeChange(db.Model):
    """Tracks scope change requests (PMBOK Scope Knowledge Area)."""

    __tablename__ = 'scope_changes'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    requested_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    change_id: str = db.Column(db.String(64), nullable=False, unique=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    justification: str = db.Column(db.Text, nullable=True)
    impact_analysis: str = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(16), nullable=False, default='draft')
    change_type: str = db.Column(db.String(16), nullable=False, default='addition')
    affected_requirements: list = db.Column(db.JSON, nullable=True)
    affected_wbs_items: list = db.Column(db.JSON, nullable=True)
    approval_date: date = db.Column(db.Date, nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('scope_changes', lazy='dynamic'))
    requester = db.relationship('User', foreign_keys=[requested_by], backref=db.backref('requested_scope_changes', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by], backref=db.backref('approved_scope_changes', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<ScopeChange {self.change_id} status={self.status}>'
