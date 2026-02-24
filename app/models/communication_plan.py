"""CommunicationPlan model for PMBOK Communication Knowledge Area."""
from datetime import datetime
from app import db

FREQUENCIES = ('daily', 'weekly', 'monthly', 'as_needed')
COMMUNICATION_METHODS = ('email', 'meeting', 'report', 'chat', 'other')
DISTRIBUTION_METHODS = ('direct', 'portal', 'other')


class CommunicationPlan(db.Model):
    """Defines the communication strategy for a project (PMBOK Communication Knowledge Area)."""

    __tablename__ = 'communication_plans'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    information: str = db.Column(db.String(256), nullable=False)
    frequency: str = db.Column(db.String(16), default='weekly', nullable=False)
    responsible: str = db.Column(db.String(128), nullable=True)
    target_audience: str = db.Column(db.String(256), nullable=True)
    communication_method: str = db.Column(db.String(32), default='email', nullable=False)
    distribution_method: str = db.Column(db.String(32), default='direct', nullable=False)
    notes: str = db.Column(db.Text, nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref=db.backref('communication_plans', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_communication_plans', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<CommunicationPlan project_id={self.project_id} information={self.information!r}>'
