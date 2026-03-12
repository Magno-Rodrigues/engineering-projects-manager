"""Add schedule sync features: ScheduleImportRecord, PEPActivity new fields, PEPActivityLog new fields

Revision ID: k1l2m3n4o5p6
Revises: j1k2l3m4n5o6
Create Date: 2026-03-12 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j1k2l3m4n5o6'
branch_labels = None
depends_on = None


def upgrade():
    # --- New table: schedule_import_records ---
    op.create_table(
        'schedule_import_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_log_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('external_task_id', sa.String(64), nullable=True),
        sa.Column('task_name', sa.String(256), nullable=False),
        sa.Column('planned_start', sa.Date(), nullable=True),
        sa.Column('planned_end', sa.Date(), nullable=True),
        sa.Column('actual_start', sa.Date(), nullable=True),
        sa.Column('actual_end', sa.Date(), nullable=True),
        sa.Column('duration_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_summary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pep_activity_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['import_log_id'], ['import_logs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pep_activity_id'], ['pep_activities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_schedule_import_records_project_id', 'schedule_import_records', ['project_id'])
    op.create_index('ix_schedule_import_records_import_log_id', 'schedule_import_records', ['import_log_id'])

    # --- Extend pep_activities with schedule sync fields ---
    op.add_column('pep_activities', sa.Column('external_task_id', sa.String(64), nullable=True))
    op.add_column('pep_activities', sa.Column('variance_percentage', sa.Numeric(8, 2), nullable=True))
    op.add_column('pep_activities', sa.Column('last_synced_at', sa.DateTime(), nullable=True))

    # --- Extend pep_activity_logs with sync tracking fields ---
    op.add_column('pep_activity_logs', sa.Column('old_value', sa.String(256), nullable=True))
    op.add_column('pep_activity_logs', sa.Column('new_value', sa.String(256), nullable=True))
    op.add_column('pep_activity_logs', sa.Column('sync_source', sa.String(32), nullable=True))


def downgrade():
    # Remove pep_activity_logs sync columns
    op.drop_column('pep_activity_logs', 'sync_source')
    op.drop_column('pep_activity_logs', 'new_value')
    op.drop_column('pep_activity_logs', 'old_value')

    # Remove pep_activities schedule sync columns
    op.drop_column('pep_activities', 'last_synced_at')
    op.drop_column('pep_activities', 'variance_percentage')
    op.drop_column('pep_activities', 'external_task_id')

    # Drop schedule_import_records table
    op.drop_index('ix_schedule_import_records_import_log_id', table_name='schedule_import_records')
    op.drop_index('ix_schedule_import_records_project_id', table_name='schedule_import_records')
    op.drop_table('schedule_import_records')
