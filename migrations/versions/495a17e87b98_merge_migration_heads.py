"""Merge migration heads

Revision ID: 495a17e87b98
Revises: 4aac511630e0, g1h2i3j4k5l6
Create Date: 2026-03-04 17:32:59.389871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '495a17e87b98'
down_revision = ('4aac511630e0', 'g1h2i3j4k5l6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
