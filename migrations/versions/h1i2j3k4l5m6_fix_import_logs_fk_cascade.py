"""Fix import_logs FK to enforce ON DELETE CASCADE.

Revision ID: h1i2j3k4l5m6
Revises: f1a2b3c4d5e6, g1h2i3j4k5l6
Create Date: 2026-03-04 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'h1i2j3k4l5m6'
down_revision = ('f1a2b3c4d5e6', 'g1h2i3j4k5l6')
branch_labels = None
depends_on = None


def upgrade():
    # Recreate the FK on import_logs.project_id with ON DELETE CASCADE.
    # batch_alter_table is used for SQLite compatibility.
    with op.batch_alter_table('import_logs') as batch_op:
        batch_op.drop_constraint('import_logs_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'import_logs_project_id_fkey',
            'projects',
            ['project_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade():
    with op.batch_alter_table('import_logs') as batch_op:
        batch_op.drop_constraint('import_logs_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'import_logs_project_id_fkey',
            'projects',
            ['project_id'],
            ['id'],
        )
