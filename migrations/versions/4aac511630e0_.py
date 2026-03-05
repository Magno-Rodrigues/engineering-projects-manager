"""Superseded migration – kept as no-op to preserve revision history.

The financial_reports and financial_scenarios tables are created by
migration k1l2m3n4o5p6 (add_financial_reports_and_scenarios), which is
the authoritative migration for those tables.  The DROP TABLE statements
in the original version of this migration referenced tables that were
never part of the current migration chain and would fail on any fresh
install; those statements have been removed.

Revision ID: 4aac511630e0
Revises: f1a2b3c4d5e6
Create Date: 2026-03-04 16:21:45.038835

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4aac511630e0'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
