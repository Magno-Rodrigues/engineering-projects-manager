"""Merge the two remaining migration heads into a single head.

This merges:
- 495a17e87b98 (merge of 4aac511630e0 no-op and g1h2i3j4k5l6
  project_cost_center pivot)
- k1l2m3n4o5p6 (add_financial_reports_and_scenarios, which also
  includes j1k2l3m4n5o6 add_source_columns and h1i2j3k4l5m6
  fix_import_logs_fk_cascade)

After this migration, `flask db upgrade` resolves to a single head and
applies all migrations in the correct topological order without
duplicate table creation.

Revision ID: l1m2n3o4p5q6
Revises: 495a17e87b98, k1l2m3n4o5p6
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l1m2n3o4p5q6'
down_revision = ('495a17e87b98', 'k1l2m3n4o5p6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
