"""create financial_scenarios table

Revision ID: 990d0e65351b
Revises: 35349ae37f5a
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = '990d0e65351b'
down_revision = 'e3f5a7b9c1d2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'financial_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_type', sa.String(length=20), nullable=False),
        sa.Column('budget_variance', sa.Numeric(5, 2), nullable=False),
        sa.Column('schedule_variance', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('financial_scenarios')