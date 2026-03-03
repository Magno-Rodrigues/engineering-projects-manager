"""ImportLog model for auditing project plan imports."""
from datetime import datetime, timezone
from app import db

IMPORT_TYPES = ('ms_project', 'primavera')
IMPORT_STATUSES = ('pending', 'success', 'failed')


class ImportLog(db.Model):
    """Audit log for imported project plans (MS Project, Primavera P6)."""

    __tablename__ = 'import_logs'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    import_type: str = db.Column(db.String(32), nullable=False)
    file_name: str = db.Column(db.String(256), nullable=False)
    status: str = db.Column(db.String(16), nullable=False, default='pending')
    total_tasks_imported: int = db.Column(db.Integer, default=0)
    total_items_imported: int = db.Column(db.Integer, default=0)
    error_message: str = db.Column(db.Text, nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('import_logs', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f'<ImportLog project_id={self.project_id} type={self.import_type} status={self.status}>'
