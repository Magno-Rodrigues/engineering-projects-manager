"""Task model."""
from datetime import datetime
from app import db


class Task(db.Model):
    """Task model for project task management."""

    __tablename__ = 'tasks'

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text)
    status: str = db.Column(db.String(32), default='todo')
    priority: str = db.Column(db.String(16), default='medium')
    due_date: datetime = db.Column(db.Date)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id: int = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs) -> None:
        """Initialize Task with default status and priority."""
        kwargs.setdefault('status', 'todo')
        kwargs.setdefault('priority', 'medium')
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f'<Task {self.title}>'
