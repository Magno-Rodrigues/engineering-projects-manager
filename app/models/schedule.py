"""Schedule management models (PMBOK - Prazo)."""
from datetime import datetime
from decimal import Decimal
from app import db


class Activity(db.Model):
    """Project activity model."""

    __tablename__ = 'activities'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    wbs_item_id: int = db.Column(db.Integer, db.ForeignKey('wbs_items.id'), nullable=True)
    code: str = db.Column(db.String(64), nullable=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    start_date: datetime = db.Column(db.Date, nullable=True)
    end_date: datetime = db.Column(db.Date, nullable=True)
    estimated_duration: int = db.Column(db.Integer, nullable=True)  # days
    actual_duration: int = db.Column(db.Integer, nullable=True)  # days
    progress: int = db.Column(db.Integer, default=0)  # 0-100 percentage
    status: str = db.Column(db.String(32), default='planned')  # planned, in_progress, completed, cancelled
    is_critical: bool = db.Column(db.Boolean, default=False)
    assignee_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predecessors = db.relationship(
        'ActivityDependency',
        foreign_keys='ActivityDependency.successor_id',
        backref='successor',
        lazy='dynamic',
    )
    successors = db.relationship(
        'ActivityDependency',
        foreign_keys='ActivityDependency.predecessor_id',
        backref='predecessor',
        lazy='dynamic',
    )

    def __repr__(self) -> str:
        return f'<Activity {self.title}>'


class ActivityDependency(db.Model):
    """Activity dependency model (FS, SS, FF, SF)."""

    __tablename__ = 'activity_dependencies'

    id: int = db.Column(db.Integer, primary_key=True)
    predecessor_id: int = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    successor_id: int = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    dependency_type: str = db.Column(db.String(8), default='FS')  # FS, SS, FF, SF
    lag: int = db.Column(db.Integer, default=0)  # lag/lead days
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ActivityDependency {self.predecessor_id}->{self.successor_id} {self.dependency_type}>'


class Milestone(db.Model):
    """Project milestone model."""

    __tablename__ = 'milestones'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    target_date: datetime = db.Column(db.Date, nullable=True)
    actual_date: datetime = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='pending')  # pending, achieved, missed
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Milestone {self.title}>'


class ScheduleBaseline(db.Model):
    """Schedule baseline model."""

    __tablename__ = 'schedule_baselines'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    baseline_start: datetime = db.Column(db.Date, nullable=True)
    baseline_end: datetime = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='active')  # draft, active, closed
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ScheduleBaseline {self.name}>'
