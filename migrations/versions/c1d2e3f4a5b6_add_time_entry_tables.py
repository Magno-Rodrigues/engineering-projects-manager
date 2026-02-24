"""Add measurement_cycles and time_entries tables

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-02-24 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # measurement_cycles table
    op.create_table('measurement_cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('start_day', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # time_entries table
    op.create_table('time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('discipline', sa.String(length=128), nullable=True),
        sa.Column('main_activity', sa.String(length=256), nullable=False),
        sa.Column('sub_activity', sa.String(length=256), nullable=True),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('hours_worked', sa.String(length=8), nullable=False),
        sa.Column('hour_type', sa.String(length=16), nullable=False, server_default='Normal'),
        sa.Column('observation', sa.Text(), nullable=True),
        sa.Column('measurement_cycle_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['measurement_cycle_id'], ['measurement_cycles.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('time_entries')
    op.drop_table('measurement_cycles')
