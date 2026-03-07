"""ProjectCharter (TAP - Termo de Abertura de Projeto) model."""
from datetime import datetime, timezone, date
from decimal import Decimal
from app import db


class ProjectCharter(db.Model):
    """Formally authorizes project creation (PMBOK Integration Knowledge Area)."""

    __tablename__ = 'project_charters'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    authorized_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    business_case: str = db.Column(db.Text, nullable=True)
    project_purpose: str = db.Column(db.Text, nullable=True)
    success_criteria: dict = db.Column(db.JSON, nullable=True)
    high_level_requirements: dict = db.Column(db.JSON, nullable=True)
    high_level_risks: dict = db.Column(db.JSON, nullable=True)
    assumptions: dict = db.Column(db.JSON, nullable=True)
    constraints: dict = db.Column(db.JSON, nullable=True)

    approved_budget: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    scheduled_start_date: date = db.Column(db.Date, nullable=True)
    scheduled_end_date: date = db.Column(db.Date, nullable=True)
    approval_date: date = db.Column(db.Date, nullable=True)

    status: str = db.Column(db.String(16), default='draft', nullable=False)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('charters', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_charters', lazy='dynamic'))
    authorizer = db.relationship('User', foreign_keys=[authorized_by], backref=db.backref('authorized_charters', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<ProjectCharter project_id={self.project_id} status={self.status}>'
