"""Financial budget models for the financial module."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db

BUDGET_CATEGORIES = ('labor', 'material', 'service', 'infrastructure', 'other')
BUDGET_STATUSES = ('active', 'revised', 'closed')


class FinancialBudget(db.Model):
    """Represents a planned budget baseline for a project."""

    __tablename__ = 'financial_budgets'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    total_planned_budget: Decimal = db.Column(db.Numeric(12, 2), nullable=False)
    currency: str = db.Column(db.String(3), default='BRL', nullable=False)
    baseline_date: datetime = db.Column(db.DateTime, nullable=False)
    status: str = db.Column(db.String(20), default='active', nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes: str = db.Column(db.Text, nullable=True)
    source: str = db.Column(db.String(32), nullable=False, default='manual', server_default='manual')

    # Relationships
    project = db.relationship('Project', backref=db.backref('financial_budgets', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by])
    items = db.relationship('FinancialBudgetItem', backref='budget', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def is_locked(self) -> bool:
        """Return True if the baseline is locked (closed status)."""
        return self.status == 'closed'

    def __repr__(self) -> str:
        return f'<FinancialBudget project_id={self.project_id} total={self.total_planned_budget}>'


class FinancialBudgetItem(db.Model):
    """Represents a line item in a financial budget."""

    __tablename__ = 'financial_budget_items'

    id: int = db.Column(db.Integer, primary_key=True)
    budget_id: int = db.Column(db.Integer, db.ForeignKey('financial_budgets.id', ondelete='CASCADE'), nullable=False)
    cost_center_id: int = db.Column(db.Integer, db.ForeignKey('cost_centers.id'), nullable=True)
    description: str = db.Column(db.String(255), nullable=False)
    planned_amount: Decimal = db.Column(db.Numeric(12, 2), nullable=False)
    category: str = db.Column(db.String(50), nullable=False, default='other')
    planned_date_start: datetime = db.Column(db.Date, nullable=True)
    planned_date_end: datetime = db.Column(db.Date, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cost_center = db.relationship('CostCenter', foreign_keys=[cost_center_id])

    def __repr__(self) -> str:
        return f'<FinancialBudgetItem description={self.description} amount={self.planned_amount}>'
