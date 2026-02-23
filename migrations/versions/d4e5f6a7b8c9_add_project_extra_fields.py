"""Add extra fields to projects table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-23 23:44:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('budget', sa.Numeric(15, 2), nullable=True))
        batch_op.add_column(sa.Column('actual_cost', sa.Numeric(15, 2), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('client_name', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('client_name')
        batch_op.drop_column('location')
        batch_op.drop_column('priority')
        batch_op.drop_column('category')
        batch_op.drop_column('actual_cost')
        batch_op.drop_column('budget')
