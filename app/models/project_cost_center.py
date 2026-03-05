"""Association model linking projects and cost centers (many-to-many)."""
from app import db


class ProjectCostCenter(db.Model):
    """Many-to-many association between projects and cost centers."""

    __tablename__ = 'project_cost_centers'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    cost_center_id: int = db.Column(db.Integer, db.ForeignKey('cost_centers.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    project = db.relationship('Project', backref=db.backref('project_cost_centers', lazy='dynamic'))
    cost_center = db.relationship('CostCenter', backref=db.backref('project_cost_centers', lazy='dynamic'))

    def __repr__(self) -> str:
        return f'<ProjectCostCenter project_id={self.project_id} cost_center_id={self.cost_center_id}>'