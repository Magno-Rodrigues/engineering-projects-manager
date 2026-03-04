"""Project model."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db


class Project(db.Model):
    """Project model for engineering project management."""

    __tablename__ = 'projects'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text)
    status: str = db.Column(db.String(32), default='planning')
    start_date: datetime = db.Column(db.Date)
    end_date: datetime = db.Column(db.Date)
    owner_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # New fields
    budget: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    actual_cost: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    category: str = db.Column(db.String(64), nullable=True)
    priority: str = db.Column(db.String(16), nullable=True)
    location: str = db.Column(db.String(256), nullable=True)
    client_name: str = db.Column(db.String(128), nullable=True)
    notes: str = db.Column(db.Text, nullable=True)

    # Relationships
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    # Read-only convenience accessor for cost centers via the pivot table.
    # Manage associations through ProjectCostCenter or CostCenterService instead.
    cost_centers = db.relationship(
        'CostCenter',
        secondary='project_cost_centers',
        lazy='dynamic',
        viewonly=True,
    )

    @property
    def remaining_budget(self):
        """Calculate remaining budget."""
        if self.budget is None:
            return None
        cost = self.actual_cost or Decimal('0')
        return self.budget - cost

    def __repr__(self) -> str:
        return f'<Project {self.name}>'
