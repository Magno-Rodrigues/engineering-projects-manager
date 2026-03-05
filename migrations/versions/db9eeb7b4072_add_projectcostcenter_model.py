"""Fix CostCenter to use many-to-many via ProjectCostCenter

Revision ID: db9eeb7b4072
Revises: f1a2b3c4d5e6
Create Date: 2026-03-05 17:01:28.252485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db9eeb7b4072'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Remove project_id from cost_centers (cost centers are now global/independent)
    with op.batch_alter_table('cost_centers', schema=None) as batch_op:
        batch_op.drop_constraint('cost_centers_project_id_fkey', type_='foreignkey')
        batch_op.drop_column('project_id')

    # Create the many-to-many association table
    op.create_table(
        'project_cost_centers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('cost_center_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'cost_center_id', name='uq_project_cost_center'),
    )


def downgrade():
    op.drop_table('project_cost_centers')

    with op.batch_alter_table('cost_centers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            'cost_centers_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )
