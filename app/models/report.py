"""Report model."""
from datetime import datetime
from app import db


class Report(db.Model):
    """Report model for project reporting."""

    __tablename__ = 'reports'

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(256), nullable=False)
    content: str = db.Column(db.Text)
    report_type: str = db.Column(db.String(32), default='progress')
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    author_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    author = db.relationship('User', backref='reports')

    def __repr__(self) -> str:
        return f'<Report {self.title}>'
