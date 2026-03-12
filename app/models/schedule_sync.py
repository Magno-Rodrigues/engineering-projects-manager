"""ScheduleImportRecord model for tracking imported schedule tasks."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db


class ScheduleImportRecord(db.Model):
    """Stores individual task records from a schedule import for EAP sync and variance analysis."""

    __tablename__ = 'schedule_import_records'

    id: int = db.Column(db.Integer, primary_key=True)
    import_log_id: int = db.Column(
        db.Integer, db.ForeignKey('import_logs.id', ondelete='CASCADE'), nullable=False
    )
    project_id: int = db.Column(
        db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    external_task_id: str = db.Column(db.String(64), nullable=True)
    task_name: str = db.Column(db.String(256), nullable=False)

    # Planned (baseline) dates from the schedule file
    planned_start = db.Column(db.Date, nullable=True)
    planned_end = db.Column(db.Date, nullable=True)

    # Actual (current) dates from the schedule file
    actual_start = db.Column(db.Date, nullable=True)
    actual_end = db.Column(db.Date, nullable=True)

    duration_hours: Decimal = db.Column(db.Numeric(10, 2), nullable=True)
    progress: int = db.Column(db.Integer, default=0, nullable=False)
    is_summary: bool = db.Column(db.Boolean, default=False, nullable=False)

    # Link to the PEPActivity created from this record (nullable until imported to EAP)
    pep_activity_id: int = db.Column(
        db.Integer, db.ForeignKey('pep_activities.id', ondelete='SET NULL'), nullable=True
    )

    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    import_log = db.relationship(
        'ImportLog', backref=db.backref('schedule_records', lazy='dynamic')
    )
    project = db.relationship(
        'Project', backref=db.backref('schedule_import_records', lazy='dynamic')
    )
    pep_activity = db.relationship('PEPActivity', foreign_keys=[pep_activity_id], lazy='joined')

    @property
    def variance_days(self) -> int:
        """Return variance in days (actual_end - planned_end). Positive = delayed."""
        if self.actual_end and self.planned_end:
            return (self.actual_end - self.planned_end).days
        return 0

    @property
    def schedule_status(self) -> str:
        """Return 'adiantada', 'no_prazo', or 'atrasada' based on date/progress comparison."""
        days = self.variance_days
        if days < -1:
            return 'adiantada'
        if days > 1:
            return 'atrasada'
        return 'no_prazo'

    def __repr__(self) -> str:
        return f'<ScheduleImportRecord project_id={self.project_id} task={self.task_name}>'
