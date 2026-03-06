"""Add indices on foreign key columns for performance

Revision ID: g1h2i3j4k5l6
Revises: db9eeb7b4072
Create Date: 2026-03-05 23:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'g1h2i3j4k5l6'
down_revision = 'db9eeb7b4072'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_financial_transactions_project_id', 'financial_transactions', ['project_id'])
    op.create_index('ix_financial_budgets_project_id', 'financial_budgets', ['project_id'])
    op.create_index('ix_project_cost_centers_project_id', 'project_cost_centers', ['project_id'])


def downgrade():
    op.drop_index('ix_financial_transactions_project_id', table_name='financial_transactions')
    op.drop_index('ix_financial_budgets_project_id', table_name='financial_budgets')
    op.drop_index('ix_project_cost_centers_project_id', table_name='project_cost_centers')
