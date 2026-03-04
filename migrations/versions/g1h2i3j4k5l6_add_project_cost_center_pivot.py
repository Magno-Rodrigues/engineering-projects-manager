"""Convert cost_center project_id to pivot table project_cost_centers

Revision ID: g1h2i3j4k5l6
Revises: e1f2a3b4c5d6
Create Date: 2026-03-04 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g1h2i3j4k5l6'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade():
    # Create the project_cost_centers pivot table
    op.create_table(
        'project_cost_centers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('cost_center_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'cost_center_id', name='uq_project_cost_center'),
    )

    # Migrate existing data: copy (project_id, id) pairs from cost_centers to pivot table
    op.execute(
        """
        INSERT INTO project_cost_centers (project_id, cost_center_id)
        SELECT project_id, id FROM cost_centers
        WHERE project_id IS NOT NULL
        """
    )

    # SQLite does not support DROP COLUMN in older versions; use batch mode
    with op.batch_alter_table('cost_centers') as batch_op:
        batch_op.drop_constraint('cost_centers_project_id_fkey', type_='foreignkey')
        batch_op.drop_column('project_id')


def downgrade():
    # Re-add project_id column to cost_centers
    with op.batch_alter_table('cost_centers') as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'cost_centers_project_id_fkey',
            'projects',
            ['project_id'],
            ['id'],
            ondelete='CASCADE',
        )

    # Restore the first project association for each cost center
    op.execute(
        """
        UPDATE cost_centers
        SET project_id = (
            SELECT project_id FROM project_cost_centers
            WHERE project_cost_centers.cost_center_id = cost_centers.id
            LIMIT 1
        )
        """
    )

    op.drop_table('project_cost_centers')
