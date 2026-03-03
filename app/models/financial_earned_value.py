"""Financial earned value (EVM) model for the financial module."""
from datetime import datetime
from decimal import Decimal
from app import db


class FinancialEarnedValue(db.Model):
    """Stores EVM (Earned Value Management) indicators for a project at a point in time."""

    __tablename__ = 'financial_earned_value'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    report_date: datetime = db.Column(db.Date, nullable=False)

    # Core EVM values
    bac: Decimal = db.Column(db.Numeric(12, 2), nullable=False)  # Budget at Completion
    ac: Decimal = db.Column(db.Numeric(12, 2), nullable=False)   # Actual Cost
    ev: Decimal = db.Column(db.Numeric(12, 2), nullable=False)   # Earned Value
    pv: Decimal = db.Column(db.Numeric(12, 2), nullable=False)   # Planned Value

    # Projections (optional, can be provided or left null to auto-calculate)
    eac: Decimal = db.Column(db.Numeric(12, 2), nullable=True)   # Estimate at Completion
    etc: Decimal = db.Column(db.Numeric(12, 2), nullable=True)   # Estimate to Complete

    notes: str = db.Column(db.Text, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'report_date', name='uq_evm_project_report_date'),
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('earned_value_reports', lazy='dynamic'))

    @property
    def cpi(self) -> float:
        """Cost Performance Index: EV / AC. >1 means under budget."""
        if self.ac and self.ac > 0:
            return float(self.ev) / float(self.ac)
        return 0.0

    @property
    def spi(self) -> float:
        """Schedule Performance Index: EV / PV. >1 means ahead of schedule."""
        if self.pv and self.pv > 0:
            return float(self.ev) / float(self.pv)
        return 0.0

    @property
    def schedule_variance(self) -> Decimal:
        """Schedule Variance: EV - PV."""
        return (self.ev or Decimal('0')) - (self.pv or Decimal('0'))

    @property
    def cost_variance(self) -> Decimal:
        """Cost Variance: EV - AC."""
        return (self.ev or Decimal('0')) - (self.ac or Decimal('0'))

    @property
    def calculated_eac(self) -> float:
        """Estimate at Completion: BAC / CPI (if not manually set)."""
        if self.eac is not None:
            return float(self.eac)
        cpi = self.cpi
        if cpi and cpi > 0:
            return float(self.bac) / cpi
        return float(self.bac) if self.bac else 0.0

    @property
    def calculated_etc(self) -> float:
        """Estimate to Complete: EAC - AC (if not manually set)."""
        if self.etc is not None:
            return float(self.etc)
        return self.calculated_eac - (float(self.ac) if self.ac else 0.0)

    def __repr__(self) -> str:
        return f'<FinancialEarnedValue project_id={self.project_id} date={self.report_date}>'
