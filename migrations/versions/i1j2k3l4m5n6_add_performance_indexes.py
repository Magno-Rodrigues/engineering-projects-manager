"""Add performance indexes on time_entries and projects

Revision ID: i1j2k3l4m5n6
Revises: h1i2j3k4l5m6
Create Date: 2026-03-10 19:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'i1j2k3l4m5n6'
down_revision = 'h1i2j3k4l5m6'
branch_labels = None
depends_on = None


def upgrade():
    # time_entries: frequently filtered columns
    op.create_index('ix_time_entries_project_id', 'time_entries', ['project_id'])
    op.create_index('ix_time_entries_user_id', 'time_entries', ['user_id'])
    op.create_index('ix_time_entries_work_date', 'time_entries', ['work_date'])

    # projects: frequently filtered columns
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_client_name', 'projects', ['client_name'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])


def downgrade():
    op.drop_index('ix_time_entries_project_id', table_name='time_entries')
    op.drop_index('ix_time_entries_user_id', table_name='time_entries')
    op.drop_index('ix_time_entries_work_date', table_name='time_entries')

    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_client_name', table_name='projects')
    op.drop_index('ix_projects_created_at', table_name='projects')
