"""Add PMBOK fields to tasks and reports tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add PMBOK fields to tasks table
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pmbok_knowledge_area', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('pmbok_process_group', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('wbs_item_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('start_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('estimated_effort', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('progress', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('dependencies', sa.Text(), nullable=True))
        batch_op.create_foreign_key('fk_tasks_wbs_item_id', 'wbs_items', ['wbs_item_id'], ['id'])

    # Add PMBOK fields to reports table
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('period_start', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('period_end', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('executive_summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('scope_complete_pct', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('schedule_variance', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('cost_variance', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('risks_identified', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('current_issues', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('completed_tasks_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('tasks_in_progress_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('next_activities', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('corrective_actions', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('attention_points', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('approved_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_reports_approved_by_id', 'users', ['approved_by_id'], ['id'])


def downgrade():
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_constraint('fk_reports_approved_by_id', type_='foreignkey')
        batch_op.drop_column('approved_by_id')
        batch_op.drop_column('attention_points')
        batch_op.drop_column('corrective_actions')
        batch_op.drop_column('next_activities')
        batch_op.drop_column('tasks_in_progress_text')
        batch_op.drop_column('completed_tasks_text')
        batch_op.drop_column('current_issues')
        batch_op.drop_column('risks_identified')
        batch_op.drop_column('cost_variance')
        batch_op.drop_column('schedule_variance')
        batch_op.drop_column('scope_complete_pct')
        batch_op.drop_column('executive_summary')
        batch_op.drop_column('period_end')
        batch_op.drop_column('period_start')
        batch_op.drop_column('report_date')

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_wbs_item_id', type_='foreignkey')
        batch_op.drop_column('dependencies')
        batch_op.drop_column('progress')
        batch_op.drop_column('estimated_effort')
        batch_op.drop_column('start_date')
        batch_op.drop_column('wbs_item_id')
        batch_op.drop_column('pmbok_process_group')
        batch_op.drop_column('pmbok_knowledge_area')
