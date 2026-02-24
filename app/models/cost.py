"""Cost management models (PMBOK - Custo)."""
from datetime import datetime
from decimal import Decimal
from app import db


class BudgetLine(db.Model):
    """Budget line model."""

    __tablename__ = 'budget_lines'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    wbs_item_id: int = db.Column(db.Integer, db.ForeignKey('wbs_items.id'), nullable=True)
    activity_id: int = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    category: str = db.Column(db.String(64), nullable=True)  # labor, material, equipment, etc.
    planned_value: Decimal = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    actual_cost: Decimal = db.Column(db.Numeric(15, 2), nullable=True, default=0)
    reference_date: datetime = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='active')  # draft, active, closed
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<BudgetLine {self.title}>'


class CostVariance(db.Model):
    """Cost variance record (Earned Value metrics)."""

    __tablename__ = 'cost_variances'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    reference_date: datetime = db.Column(db.Date, nullable=False)
    planned_value: Decimal = db.Column(db.Numeric(15, 2), default=0)   # PV
    earned_value: Decimal = db.Column(db.Numeric(15, 2), default=0)    # EV
    actual_cost: Decimal = db.Column(db.Numeric(15, 2), default=0)     # AC
    notes: str = db.Column(db.Text, nullable=True)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def cost_variance(self):
        """CV = EV - AC."""
        ev = self.earned_value or Decimal('0')
        ac = self.actual_cost or Decimal('0')
        return ev - ac

    @property
    def schedule_variance(self):
        """SV = EV - PV."""
        ev = self.earned_value or Decimal('0')
        pv = self.planned_value or Decimal('0')
        return ev - pv

    @property
    def cpi(self):
        """CPI = EV / AC."""
        ac = self.actual_cost or Decimal('0')
        if ac == 0:
            return None
        return (self.earned_value or Decimal('0')) / ac

    @property
    def spi(self):
        """SPI = EV / PV."""
        pv = self.planned_value or Decimal('0')
        if pv == 0:
            return None
        return (self.earned_value or Decimal('0')) / pv

    def __repr__(self) -> str:
        return f'<CostVariance {self.reference_date}>'


class CostBaseline(db.Model):
    """Cost baseline model (Curva S)."""

    __tablename__ = 'cost_baselines'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    total_budget: Decimal = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    status: str = db.Column(db.String(32), default='active')  # draft, active, closed
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<CostBaseline {self.name}>'
