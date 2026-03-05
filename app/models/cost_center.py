"""Cost center model for financial module."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db


class CostCenter(db.Model):
    """Represents a cost center for budget allocation.

    Projects are associated with cost centers via the ``project_cost_centers``
    association table (many-to-many relationship).
    """

    __tablename__ = 'cost_centers'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    manager_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    budget_allocation: Decimal = db.Column(db.Numeric(12, 2), nullable=True)
    status: str = db.Column(db.String(20), default='active', nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    manager = db.relationship('User', foreign_keys=[manager_id])

    def __repr__(self) -> str:
        return f'<CostCenter name={self.name}>'
