"""Add source column to tasks, wbs_items, and financial_budgets to track import origin.

Revision ID: j1k2l3m4n5o6
Revises: h1i2j3k4l5m6
Create Date: 2026-03-04 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'j1k2l3m4n5o6'
down_revision = 'h1i2j3k4l5m6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.add_column(
            sa.Column('source', sa.String(32), nullable=False, server_default='manual')
        )

    with op.batch_alter_table('wbs_items') as batch_op:
        batch_op.add_column(
            sa.Column('source', sa.String(32), nullable=False, server_default='manual')
        )

    with op.batch_alter_table('financial_budgets') as batch_op:
        batch_op.add_column(
            sa.Column('source', sa.String(32), nullable=False, server_default='manual')
        )


def downgrade():
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_column('source')

    with op.batch_alter_table('wbs_items') as batch_op:
        batch_op.drop_column('source')

    with op.batch_alter_table('financial_budgets') as batch_op:
        batch_op.drop_column('source')
