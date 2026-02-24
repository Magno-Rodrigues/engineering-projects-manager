"""Stakeholder model for PMBOK Stakeholder Knowledge Area."""
from datetime import datetime
from app import db

INTEREST_LEVELS = ('high', 'medium', 'low')
INFLUENCE_LEVELS = ('high', 'medium', 'low')
STAKEHOLDER_CATEGORIES = ('sponsor', 'customer', 'team', 'supplier', 'regulator', 'other')


class Stakeholder(db.Model):
    """Represents a project stakeholder (PMBOK Stakeholder Knowledge Area)."""

    __tablename__ = 'stakeholders'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    name: str = db.Column(db.String(128), nullable=False)
    role: str = db.Column(db.String(128), nullable=True)
    organization: str = db.Column(db.String(128), nullable=True)
    email: str = db.Column(db.String(256), nullable=True)
    phone: str = db.Column(db.String(64), nullable=True)

    interest_level: str = db.Column(db.String(16), default='medium', nullable=False)
    influence_level: str = db.Column(db.String(16), default='medium', nullable=False)
    category: str = db.Column(db.String(32), default='other', nullable=False)

    engagement_strategy: str = db.Column(db.Text, nullable=True)
    communication_preference: str = db.Column(db.String(128), nullable=True)
    notes: str = db.Column(db.Text, nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref=db.backref('stakeholders', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<Stakeholder name={self.name} project_id={self.project_id}>'
