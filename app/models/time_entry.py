"""Time entry and measurement cycle models."""
import re
from datetime import datetime, timezone
from app import db

HOUR_TYPES = ['Normal', 'Extra']


class MeasurementCycle(db.Model):
    """Measurement cycle model for controlling time-entry periods."""

    __tablename__ = 'measurement_cycles'

    id: int = db.Column(db.Integer, primary_key=True)
    start_day: int = db.Column(db.Integer, nullable=False)
    start_date: datetime = db.Column(db.Date, nullable=False)
    end_date: datetime = db.Column(db.Date, nullable=False)
    is_active: bool = db.Column(db.Boolean, default=False, nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    time_entries = db.relationship('TimeEntry', backref='measurement_cycle', lazy='dynamic',
                                   cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f'<MeasurementCycle {self.start_date} - {self.end_date}>'


class TimeEntry(db.Model):
    """Time entry model for tracking hours worked on projects."""

    __tablename__ = 'time_entries'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    discipline: str = db.Column(db.String(128), nullable=True)
    main_activity: str = db.Column(db.String(256), nullable=False)
    sub_activity: str = db.Column(db.String(256), nullable=True)
    work_date: datetime = db.Column(db.Date, nullable=False)
    hours_worked: str = db.Column(db.String(8), nullable=False)
    hour_type: str = db.Column(db.String(16), nullable=False, default='Normal')
    observation: str = db.Column(db.Text, nullable=True)
    measurement_cycle_id: int = db.Column(db.Integer, db.ForeignKey('measurement_cycles.id'), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', foreign_keys=[project_id])
    user = db.relationship('User', foreign_keys=[user_id])

    @staticmethod
    def is_valid_hours(value: str) -> bool:
        """Validate hours in HH:MM:SS format."""
        return bool(re.match(r'^\d{2}:\d{2}:\d{2}$', value or ''))

    def __repr__(self) -> str:
        return f'<TimeEntry {self.work_date} {self.hours_worked}>'
