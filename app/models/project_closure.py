"""ProjectClosure model for project closing and lessons learned."""
from datetime import datetime, timezone, date
from decimal import Decimal
from app import db


class ProjectClosure(db.Model):
    """Documents project closing and captures lessons learned (PMBOK Integration Knowledge Area)."""

    __tablename__ = 'project_closures'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    actual_end_date: date = db.Column(db.Date, nullable=True)
    actual_final_cost: Decimal = db.Column(db.Numeric(15, 2), nullable=True)

    project_results_summary: str = db.Column(db.Text, nullable=True)
    deliverables_status: dict = db.Column(db.JSON, nullable=True)
    lessons_learned: str = db.Column(db.Text, nullable=True)
    recommendations: str = db.Column(db.Text, nullable=True)

    closure_status: str = db.Column(db.String(16), default='draft', nullable=False)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('closures', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_closures', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by], backref=db.backref('approved_closures', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<ProjectClosure project_id={self.project_id} status={self.closure_status}>'
