"""Add module permission system

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-23 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'module_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_name', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=64), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_name'),
    )

    op.create_table(
        'user_module_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module_name', sa.String(length=64), nullable=False),
        sa.Column('can_create', sa.Boolean(), nullable=True),
        sa.Column('can_read', sa.Boolean(), nullable=True),
        sa.Column('can_update', sa.Boolean(), nullable=True),
        sa.Column('can_delete', sa.Boolean(), nullable=True),
        sa.Column('granted_by_id', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_name', name='uq_user_module'),
    )

    # Seed the initial 'projects' module
    op.execute(
        "INSERT INTO module_permissions (module_name, display_name, description, icon, is_active) "
        "VALUES ('projects', 'Projetos', 'Gerenciamento de projetos', 'folder', 1)"
    )


def downgrade():
    op.drop_table('user_module_permissions')
    op.drop_table('module_permissions')
