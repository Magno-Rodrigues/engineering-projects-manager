"""Financial transaction model for the financial module."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db

TRANSACTION_TYPES = ('expense', 'revenue', 'payment', 'receipt')
TRANSACTION_CATEGORIES = ('labor', 'material', 'service', 'infrastructure', 'other')
PAYMENT_STATUSES = ('pending', 'completed', 'cancelled')
PAYMENT_METHODS = ('cash', 'check', 'transfer', 'credit_card', 'debit_card', 'other')


class FinancialTransaction(db.Model):
    """Represents a financial transaction (expense or revenue) for a project."""

    __tablename__ = 'financial_transactions'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    cost_center_id: int = db.Column(db.Integer, db.ForeignKey('cost_centers.id'), nullable=True)
    type: str = db.Column(db.String(20), nullable=False)
    description: str = db.Column(db.String(255), nullable=False)
    amount: Decimal = db.Column(db.Numeric(12, 2), nullable=False)
    category: str = db.Column(db.String(50), nullable=False, default='other')
    transaction_date: datetime = db.Column(db.Date, nullable=False)
    payment_status: str = db.Column(db.String(20), default='pending', nullable=False)
    payment_method: str = db.Column(db.String(50), nullable=True)
    supplier_id: int = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    invoice_number: str = db.Column(db.String(50), nullable=True)
    reference_document: str = db.Column(db.String(100), nullable=True)
    notes: str = db.Column(db.Text, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'invoice_number', name='uq_transaction_project_invoice'),
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('financial_transactions', lazy='dynamic'))
    cost_center = db.relationship('CostCenter', foreign_keys=[cost_center_id], lazy='joined')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], lazy='joined')
    creator = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<FinancialTransaction type={self.type} amount={self.amount} date={self.transaction_date}>'
