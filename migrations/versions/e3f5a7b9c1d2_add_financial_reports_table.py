"""Add financial_reports table

Revision ID: e3f5a7b9c1d2
Revises: d2f4a6b8c0e1
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3f5a7b9c1d2"
down_revision = "d2f4a6b8c0e1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "financial_reports" in inspector.get_table_names():
        return

    op.create_table(
        "financial_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("generated_by", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("format", sa.String(length=10), nullable=False, server_default="xlsx"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
    )
    op.create_index("ix_financial_reports_project_id", "financial_reports", ["project_id"])


def downgrade():
    op.drop_table("financial_reports")

