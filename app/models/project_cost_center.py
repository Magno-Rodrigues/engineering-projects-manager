"""Association model linking projects and cost centers (many-to-many)."""
from app import db


class ProjectCostCenter(db.Model):
    """Pivot table associating projects with cost centers.

    Allows a cost center to be shared across multiple projects.
    """

    __tablename__ = 'project_cost_centers'

    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(
        db.Integer,
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
    )
    cost_center_id: int = db.Column(
        db.Integer,
        db.ForeignKey('cost_centers.id', ondelete='CASCADE'),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint('project_id', 'cost_center_id', name='uq_project_cost_center'),
    )

    # Relationships
    # Backref cascades only deletions; the DB-level ondelete='CASCADE' on the FKs
    # ensures rows are removed automatically when a project or cost center is deleted.
    project = db.relationship('Project', backref=db.backref('project_cost_centers', lazy='dynamic', cascade='all, delete-orphan'))
    cost_center = db.relationship('CostCenter', backref=db.backref('project_cost_centers', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self) -> str:
        return f'<ProjectCostCenter project_id={self.project_id} cost_center_id={self.cost_center_id}>'
