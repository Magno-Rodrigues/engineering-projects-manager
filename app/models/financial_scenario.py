"""Financial scenario model."""
from datetime import datetime
from app import db

SCENARIO_TYPES = ('pessimistic', 'realistic', 'optimistic')


class FinancialScenario(db.Model):
    """Stores financial simulation scenarios for a project."""
    __tablename__ = 'financial_scenarios'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(20), nullable=False, default='realistic')
    budget_variance = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    schedule_variance = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project = db.relationship('Project', backref=db.backref('financial_scenarios', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<FinancialScenario name={self.name} type={self.scenario_type}>'
