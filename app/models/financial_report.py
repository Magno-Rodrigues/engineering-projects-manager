"""Financial report model."""
from datetime import datetime
from app import db

REPORT_TYPES = ('executive', 'detailed', 'evm', 'cash_flow')
REPORT_FORMATS = ('pdf', 'xlsx', 'html')
REPORT_STATUSES = ('draft', 'finalized')


class FinancialReport(db.Model):
    """Stores generated financial reports for a project."""
    __tablename__ = 'financial_reports'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    format = db.Column(db.String(10), nullable=False, default='xlsx')
    status = db.Column(db.String(20), nullable=False, default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project = db.relationship('Project', backref=db.backref('financial_reports', lazy='dynamic'))
    generator = db.relationship('User', foreign_keys=[generated_by])

    def __repr__(self):
        return f'<FinancialReport type={self.report_type} project_id={self.project_id}>'
