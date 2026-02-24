"""Add extended profile fields to users table

Revision ID: a2f3c4d5e6f7
Revises: 35349ae37f5a
Create Date: 2026-02-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2f3c4d5e6f7'
down_revision = '35349ae37f5a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('job_title', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('company', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('supervisor', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('birth_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('appointment_start_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('measurement_criterion', sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('measurement_criterion')
        batch_op.drop_column('appointment_start_date')
        batch_op.drop_column('birth_date')
        batch_op.drop_column('supervisor')
        batch_op.drop_column('company')
        batch_op.drop_column('job_title')
        batch_op.drop_column('phone')
