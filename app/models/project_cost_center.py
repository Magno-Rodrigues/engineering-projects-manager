"""Association model between projects and cost centers."""
from app import db


class ProjectCostCenter(db.Model):
    """Many-to-many association between a project and a cost center.

    A project can have multiple cost centers and a cost center can be
    shared across projects via this association table.
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
    project = db.relationship(
        'Project',
        backref=db.backref('project_cost_centers', lazy='select', cascade='save-update, merge, delete'),
    )
    cost_center = db.relationship(
        'CostCenter',
        backref=db.backref('project_cost_centers', lazy='select', cascade='save-update, merge, delete'),
    )

    def __repr__(self) -> str:
        return f'<ProjectCostCenter project_id={self.project_id} cost_center_id={self.cost_center_id}>'
