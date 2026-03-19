"""add financial_scenarios table"""

from alembic import op
import sqlalchemy as sa

# --- Essencial para Alembic ---
revision = 'c3576779fda5'           # ID desta migration
down_revision = '86c6a9e12ddd'      # ID da migration imediatamente anterior
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'financial_scenarios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_type', sa.String(20), nullable=False, server_default='realistic'),
        sa.Column('budget_variance', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('schedule_variance', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_table('financial_scenarios')