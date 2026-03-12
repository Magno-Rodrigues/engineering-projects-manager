"""PEP (Project Execution Plan) models."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db


# ---------------------------------------------------------------------------
# EAP (Estrutura Analítica do Projeto) models
# ---------------------------------------------------------------------------

class PEPPhase(db.Model):
    """A top-level phase in the project's EAP hierarchy."""

    __tablename__ = 'pep_phases'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='pending', nullable=False)
    sequence: int = db.Column(db.Integer, default=0, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('pep_phases', lazy='dynamic'))
    stages = db.relationship(
        'PEPStage', backref='phase', lazy='dynamic', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<PEPPhase {self.name}>'


class PEPStage(db.Model):
    """A stage within a project phase."""

    __tablename__ = 'pep_stages'

    id: int = db.Column(db.Integer, primary_key=True)
    phase_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_phases.id', ondelete='CASCADE'), nullable=False
    )
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='pending', nullable=False)
    sequence: int = db.Column(db.Integer, default=0, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    activities = db.relationship(
        'PEPActivity', backref='stage', lazy='dynamic', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<PEPStage {self.name}>'


class PEPActivity(db.Model):
    """An activity within a project stage."""

    __tablename__ = 'pep_activities'

    id: int = db.Column(db.Integer, primary_key=True)
    stage_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_stages.id', ondelete='CASCADE'), nullable=False
    )
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    duration_hours: Decimal = db.Column(db.Numeric(10, 2), nullable=True)
    responsible_user_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    status: str = db.Column(db.String(32), default='pending', nullable=False)
    progress: int = db.Column(db.Integer, default=0, nullable=False)
    dependencies: str = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    # Schedule sync fields
    external_task_id: str = db.Column(db.String(64), nullable=True)
    variance_percentage: Decimal = db.Column(db.Numeric(8, 2), nullable=True)
    last_synced_at: datetime = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    responsible_user = db.relationship('User', foreign_keys=[responsible_user_id], lazy='joined')
    logs = db.relationship(
        'PEPActivityLog', backref='activity', lazy='dynamic', cascade='all, delete-orphan'
    )
    allocations = db.relationship(
        'PEPResourceAllocation', backref='activity', lazy='dynamic', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<PEPActivity {self.name}>'


class PEPActivityLog(db.Model):
    """Audit log for changes to a PEP activity."""

    __tablename__ = 'pep_activity_logs'

    id: int = db.Column(db.Integer, primary_key=True)
    activity_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_activities.id', ondelete='CASCADE'), nullable=False
    )
    change_description: str = db.Column(db.Text, nullable=False)
    old_value: str = db.Column(db.String(256), nullable=True)
    new_value: str = db.Column(db.String(256), nullable=True)
    sync_source: str = db.Column(db.String(32), nullable=True)  # 'eap' or 'schedule'
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    author = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPActivityLog activity_id={self.activity_id}>'


# ---------------------------------------------------------------------------
# Risk Management models
# ---------------------------------------------------------------------------

class PEPRisk(db.Model):
    """A project risk registered in the risk matrix."""

    __tablename__ = 'pep_risks'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    description: str = db.Column(db.Text, nullable=False)
    probability: int = db.Column(db.Integer, nullable=False)  # 1-5
    impact: int = db.Column(db.Integer, nullable=False)       # 1-5
    status: str = db.Column(db.String(32), default='identified', nullable=False)
    mitigation_plan: str = db.Column(db.Text, nullable=True)
    owner_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('pep_risks', lazy='dynamic'))
    owner = db.relationship('User', foreign_keys=[owner_id], lazy='joined')
    risk_logs = db.relationship(
        'PEPRiskLog', backref='risk', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def risk_level(self) -> int:
        """Return risk level as probability * impact (1-25)."""
        return self.probability * self.impact

    @property
    def risk_color(self) -> str:
        """Return CSS color class based on risk level."""
        level = self.risk_level
        if level <= 5:
            return 'green'
        if level <= 12:
            return 'yellow'
        return 'red'

    def __repr__(self) -> str:
        return f'<PEPRisk project_id={self.project_id} level={self.risk_level}>'


class PEPRiskLog(db.Model):
    """Historical tracking of risk changes."""

    __tablename__ = 'pep_risk_logs'

    id: int = db.Column(db.Integer, primary_key=True)
    risk_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_risks.id', ondelete='CASCADE'), nullable=False
    )
    change_description: str = db.Column(db.Text, nullable=False)
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    author = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPRiskLog risk_id={self.risk_id}>'


# ---------------------------------------------------------------------------
# Resource Allocation models
# ---------------------------------------------------------------------------

class PEPResourceAllocation(db.Model):
    """Allocation of a team member to a PEP activity."""

    __tablename__ = 'pep_resource_allocations'

    id: int = db.Column(db.Integer, primary_key=True)
    activity_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_activities.id', ondelete='CASCADE'), nullable=False
    )
    user_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    allocated_hours: Decimal = db.Column(db.Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPResourceAllocation activity_id={self.activity_id} user_id={self.user_id}>'


class PEPResourceCapacity(db.Model):
    """Capacity definition for a team member."""

    __tablename__ = 'pep_resource_capacities'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    available_hours_per_day: Decimal = db.Column(db.Numeric(5, 2), nullable=False, default=8)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPResourceCapacity user_id={self.user_id}>'


# ---------------------------------------------------------------------------
# Baseline & Monitoring models
# ---------------------------------------------------------------------------

class PEPBaseline(db.Model):
    """Frozen baseline snapshot for a project."""

    __tablename__ = 'pep_baselines'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    name: str = db.Column(db.String(128), nullable=False, default='Baseline')
    total_cost: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    total_duration: int = db.Column(db.Integer, nullable=True)  # in days
    baseline_date = db.Column(db.Date, nullable=False)
    status: str = db.Column(db.String(32), default='active', nullable=False)
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('pep_baselines', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], lazy='joined')
    variations = db.relationship(
        'PEPVariation', backref='baseline', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def is_locked(self) -> bool:
        """Return True if baseline is locked."""
        return self.status == 'locked'

    def __repr__(self) -> str:
        return f'<PEPBaseline project_id={self.project_id} name={self.name}>'


class PEPVariation(db.Model):
    """A recorded variation from the baseline."""

    __tablename__ = 'pep_variations'

    id: int = db.Column(db.Integer, primary_key=True)
    baseline_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_baselines.id', ondelete='CASCADE'), nullable=False
    )
    activity_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_activities.id', ondelete='SET NULL'), nullable=True
    )
    original_value: Decimal = db.Column(db.Numeric(15, 2), nullable=False)
    current_value: Decimal = db.Column(db.Numeric(15, 2), nullable=False)
    variation_type: str = db.Column(db.String(32), nullable=False)  # scope/schedule/cost
    description: str = db.Column(db.Text, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    activity = db.relationship('PEPActivity', foreign_keys=[activity_id], lazy='joined')

    @property
    def variance(self) -> Decimal:
        """Return the variance (current - original)."""
        return self.current_value - self.original_value

    @property
    def variance_pct(self) -> float:
        """Return variance as a percentage of original value."""
        if not self.original_value:
            return 0.0
        return float((self.current_value - self.original_value) / self.original_value * 100)

    def __repr__(self) -> str:
        return f'<PEPVariation baseline_id={self.baseline_id} type={self.variation_type}>'


# ---------------------------------------------------------------------------
# Documentation & History models
# ---------------------------------------------------------------------------

class PEPDecisionLog(db.Model):
    """A recorded project decision."""

    __tablename__ = 'pep_decision_logs'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    decision: str = db.Column(db.Text, nullable=False)
    justification: str = db.Column(db.Text, nullable=True)
    owner_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('pep_decision_logs', lazy='dynamic'))
    owner = db.relationship('User', foreign_keys=[owner_id], lazy='joined')
    author = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPDecisionLog project_id={self.project_id}>'


class PEPChangeLog(db.Model):
    """Audit trail for PEP entity changes."""

    __tablename__ = 'pep_change_logs'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    entity_type: str = db.Column(db.String(64), nullable=False)
    change_description: str = db.Column(db.Text, nullable=False)
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = db.relationship('Project', backref=db.backref('pep_change_logs', lazy='dynamic'))
    author = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPChangeLog project_id={self.project_id} entity={self.entity_type}>'


class PEPComment(db.Model):
    """A comment attached to any PEP entity."""

    __tablename__ = 'pep_comments'

    id: int = db.Column(db.Integer, primary_key=True)
    entity_type: str = db.Column(db.String(64), nullable=False)
    entity_id: int = db.Column(db.Integer, nullable=False)
    content: str = db.Column(db.Text, nullable=False)
    created_by: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    author = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def __repr__(self) -> str:
        return f'<PEPComment entity={self.entity_type}:{self.entity_id}>'
