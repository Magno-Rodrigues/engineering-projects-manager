"""Report model."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db

# Report types
REPORT_TYPES = [
    ('progress', 'Progresso'),
    ('technical', 'Técnico'),
    ('risk', 'Risco'),
    ('final', 'Final'),
]


class Report(db.Model):
    """Report model for project reporting."""

    __tablename__ = 'reports'

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(256), nullable=False)
    content: str = db.Column(db.Text)
    report_type: str = db.Column(db.String(32), default='progress')
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    author_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # PMBOK fields
    report_date: datetime = db.Column(db.Date, nullable=True)
    period_start: datetime = db.Column(db.Date, nullable=True)
    period_end: datetime = db.Column(db.Date, nullable=True)
    executive_summary: str = db.Column(db.Text, nullable=True)
    scope_complete_pct: Decimal = db.Column(db.Numeric(5, 2), nullable=True)
    schedule_variance: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    cost_variance: Decimal = db.Column(db.Numeric(15, 2), nullable=True)
    risks_identified: str = db.Column(db.Text, nullable=True)
    current_issues: str = db.Column(db.Text, nullable=True)
    completed_tasks_text: str = db.Column(db.Text, nullable=True)
    tasks_in_progress_text: str = db.Column(db.Text, nullable=True)
    next_activities: str = db.Column(db.Text, nullable=True)
    corrective_actions: str = db.Column(db.Text, nullable=True)
    attention_points: str = db.Column(db.Text, nullable=True)
    approved_by_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], backref='reports')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_reports')

    def __repr__(self) -> str:
        return f'<Report {self.title}>'
