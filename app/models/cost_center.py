"""Cost center model for financial module."""
from datetime import datetime
from decimal import Decimal
from app import db


class CostCenter(db.Model):
    """Represents a cost center for budget allocation within a project."""

    __tablename__ = 'cost_centers'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name: str = db.Column(db.String(100), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    manager_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    budget_allocation: Decimal = db.Column(db.Numeric(12, 2), nullable=True)
    status: str = db.Column(db.String(20), default='active', nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref=db.backref('cost_centers', lazy='dynamic'))
    manager = db.relationship('User', foreign_keys=[manager_id])

    def __repr__(self) -> str:
        return f'<CostCenter name={self.name} project_id={self.project_id}>'
