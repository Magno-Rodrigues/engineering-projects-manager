"""Requirement model for PMBOK Scope Knowledge Area."""
from datetime import datetime, timezone
from app import db


class Requirement(db.Model):
    """Documents project requirements (PMBOK Scope Knowledge Area)."""

    __tablename__ = 'requirements'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    requirement_id: str = db.Column(db.String(64), nullable=False, unique=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    category: str = db.Column(db.String(32), nullable=False, default='functional')
    priority: str = db.Column(db.String(16), nullable=False, default='medium')
    status: str = db.Column(db.String(16), nullable=False, default='draft')
    acceptance_criteria: dict = db.Column(db.JSON, nullable=True)
    source: str = db.Column(db.String(256), nullable=True)
    trace_to_wbs_items: list = db.Column(db.JSON, nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('requirements', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_requirements', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<Requirement {self.requirement_id} status={self.status}>'
