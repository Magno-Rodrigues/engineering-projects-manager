"""WBSItem model for PMBOK Scope Knowledge Area."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db


class WBSItem(db.Model):
    """Work Breakdown Structure decomposition (PMBOK Scope Knowledge Area)."""

    __tablename__ = 'wbs_items'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_by: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id: int = db.Column(db.Integer, db.ForeignKey('wbs_items.id'), nullable=True)
    responsible_user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    wbs_code: str = db.Column(db.String(64), nullable=False)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    level: int = db.Column(db.Integer, nullable=False, default=1)
    status: str = db.Column(db.String(16), nullable=False, default='planning')
    estimated_effort: Decimal = db.Column(db.Numeric(10, 2), nullable=True)
    actual_effort: Decimal = db.Column(db.Numeric(10, 2), nullable=True)

    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', backref=db.backref('wbs_items', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_wbs_items', lazy='dynamic'))
    responsible = db.relationship('User', foreign_keys=[responsible_user_id], backref=db.backref('responsible_wbs_items', lazy='dynamic'))
    children = db.relationship('WBSItem', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self) -> str:
        return f'<WBSItem {self.wbs_code} status={self.status}>'
