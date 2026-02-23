"""Add password_reset_required, last_login, and password_reset_tokens table

Revision ID: a1b2c3d4e5f6
Revises: 35349ae37f5a
Create Date: 2026-02-23 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '35349ae37f5a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_reset_required', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )


def downgrade():
    op.drop_table('password_reset_tokens')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('password_reset_required')
