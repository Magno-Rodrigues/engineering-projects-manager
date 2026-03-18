"""Add missing user profile fields (Render hotfix)

Revision ID: c8d3a1f2e9b4
Revises: c7a9d2e4f1b0
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8d3a1f2e9b4"
down_revision = "c7a9d2e4f1b0"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(table_name)}
    if column.name not in existing:
        op.add_column(table_name, column)


def upgrade():
    # These fields exist in app/models/user.py but weren't present in early migrations.
    _add_column_if_missing("users", sa.Column("phone", sa.String(length=20), nullable=True))
    _add_column_if_missing("users", sa.Column("supervision", sa.String(length=64), nullable=True))
    _add_column_if_missing("users", sa.Column("function", sa.String(length=128), nullable=True))
    _add_column_if_missing("users", sa.Column("company", sa.String(length=64), nullable=True))
    _add_column_if_missing("users", sa.Column("state", sa.String(length=2), nullable=True))
    _add_column_if_missing("users", sa.Column("measurement_criteria", sa.String(length=64), nullable=True))
    _add_column_if_missing("users", sa.Column("birth_date", sa.Date(), nullable=True))
    _add_column_if_missing("users", sa.Column("start_appointment_date", sa.Date(), nullable=True))
    _add_column_if_missing("users", sa.Column("last_login", sa.DateTime(), nullable=True))


def downgrade():
    # Best-effort: drop only if present.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns("users")}

    for col in [
        "last_login",
        "start_appointment_date",
        "birth_date",
        "measurement_criteria",
        "state",
        "company",
        "function",
        "supervision",
        "phone",
    ]:
        if col in existing:
            op.drop_column("users", col)

