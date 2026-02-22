"""Project model."""
from datetime import datetime
from app import db


class Project(db.Model):
    """Project model for engineering project management."""

    __tablename__ = 'projects'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(128), nullable=False)
    description: str = db.Column(db.Text)
    status: str = db.Column(db.String(32), default='planning')
    start_date: datetime = db.Column(db.Date)
    end_date: datetime = db.Column(db.Date)
    owner_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Project {self.name}>'
