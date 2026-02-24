"""Add PMBOK knowledge area tables: charter, closure, scope, stakeholders, communication plan

Revision ID: a1b2c3d4e5f6
Revises: eb6013d3c3e0
Create Date: 2026-02-24 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eb6013d3c3e0'
branch_labels = None
depends_on = None


def upgrade():
    # project_charters table
    op.create_table('project_charters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('authorized_by', sa.Integer(), nullable=True),
        sa.Column('business_case', sa.Text(), nullable=True),
        sa.Column('project_purpose', sa.Text(), nullable=True),
        sa.Column('success_criteria', sa.JSON(), nullable=True),
        sa.Column('high_level_requirements', sa.JSON(), nullable=True),
        sa.Column('high_level_risks', sa.JSON(), nullable=True),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('constraints', sa.JSON(), nullable=True),
        sa.Column('approved_budget', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('scheduled_start_date', sa.Date(), nullable=True),
        sa.Column('scheduled_end_date', sa.Date(), nullable=True),
        sa.Column('approval_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['authorized_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # project_closures table
    op.create_table('project_closures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('actual_final_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('project_results_summary', sa.Text(), nullable=True),
        sa.Column('deliverables_status', sa.JSON(), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('closure_status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # requirements table
    op.create_table('requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('requirement_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('priority', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('acceptance_criteria', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=256), nullable=True),
        sa.Column('trace_to_wbs_items', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('requirement_id')
    )

    # wbs_items table
    op.create_table('wbs_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('responsible_user_id', sa.Integer(), nullable=True),
        sa.Column('wbs_code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('estimated_effort', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('actual_effort', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['wbs_items.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['responsible_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # scope_changes table
    op.create_table('scope_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('change_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('impact_analysis', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('change_type', sa.String(length=16), nullable=False),
        sa.Column('affected_requirements', sa.JSON(), nullable=True),
        sa.Column('affected_wbs_items', sa.JSON(), nullable=True),
        sa.Column('approval_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('change_id')
    )

    # stakeholders table
    op.create_table('stakeholders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=128), nullable=True),
        sa.Column('organization', sa.String(length=128), nullable=True),
        sa.Column('email', sa.String(length=256), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('interest_level', sa.String(length=16), nullable=False),
        sa.Column('influence_level', sa.String(length=16), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('engagement_strategy', sa.Text(), nullable=True),
        sa.Column('communication_preference', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # communication_plans table
    op.create_table('communication_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('information', sa.String(length=256), nullable=False),
        sa.Column('frequency', sa.String(length=16), nullable=False),
        sa.Column('responsible', sa.String(length=128), nullable=True),
        sa.Column('target_audience', sa.String(length=256), nullable=True),
        sa.Column('communication_method', sa.String(length=32), nullable=False),
        sa.Column('distribution_method', sa.String(length=32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('communication_plans')
    op.drop_table('stakeholders')
    op.drop_table('scope_changes')
    op.drop_table('wbs_items')
    op.drop_table('requirements')
    op.drop_table('project_closures')
    op.drop_table('project_charters')
