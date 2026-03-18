"""Add PEP (Project Execution Plan) tables

Revision ID: d2f4a6b8c0e1
Revises: c8d3a1f2e9b4
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f4a6b8c0e1"
down_revision = "c8d3a1f2e9b4"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return name in inspector.get_table_names()


def upgrade():
    # EAP hierarchy
    if not _has_table("pep_phases"):
        op.create_table(
            "pep_phases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_pep_phases_project_id", "pep_phases", ["project_id"])

    if not _has_table("pep_stages"):
        op.create_table(
            "pep_stages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("phase_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["phase_id"], ["pep_phases.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_pep_stages_phase_id", "pep_stages", ["phase_id"])

    if not _has_table("pep_activities"):
        op.create_table(
            "pep_activities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("stage_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("duration_hours", sa.Numeric(10, 2), nullable=True),
            sa.Column("responsible_user_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("dependencies", sa.Text(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["stage_id"], ["pep_stages.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_activities_stage_id", "pep_activities", ["stage_id"])
        op.create_index(
            "ix_pep_activities_responsible_user_id", "pep_activities", ["responsible_user_id"]
        )

    if not _has_table("pep_activity_logs"):
        op.create_table(
            "pep_activity_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("activity_id", sa.Integer(), nullable=False),
            sa.Column("change_description", sa.Text(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["activity_id"], ["pep_activities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_activity_logs_activity_id", "pep_activity_logs", ["activity_id"])

    # Risks
    if not _has_table("pep_risks"):
        op.create_table(
            "pep_risks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("probability", sa.Integer(), nullable=False),
            sa.Column("impact", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="identified"),
            sa.Column("mitigation_plan", sa.Text(), nullable=True),
            sa.Column("owner_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_risks_project_id", "pep_risks", ["project_id"])

    if not _has_table("pep_risk_logs"):
        op.create_table(
            "pep_risk_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("risk_id", sa.Integer(), nullable=False),
            sa.Column("change_description", sa.Text(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["risk_id"], ["pep_risks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_risk_logs_risk_id", "pep_risk_logs", ["risk_id"])

    # Resource allocation / capacity
    if not _has_table("pep_resource_allocations"):
        op.create_table(
            "pep_resource_allocations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("activity_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("allocated_hours", sa.Numeric(10, 2), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["activity_id"], ["pep_activities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_pep_resource_allocations_activity_id",
            "pep_resource_allocations",
            ["activity_id"],
        )

    if not _has_table("pep_resource_capacities"):
        op.create_table(
            "pep_resource_capacities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column(
                "available_hours_per_day", sa.Numeric(5, 2), nullable=False, server_default="8"
            ),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_pep_resource_capacities_user_id", "pep_resource_capacities", ["user_id"])

    # Baselines / variations
    if not _has_table("pep_baselines"):
        op.create_table(
            "pep_baselines",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False, server_default="Baseline"),
            sa.Column("total_cost", sa.Numeric(15, 2), nullable=True),
            sa.Column("total_duration", sa.Integer(), nullable=True),
            sa.Column("baseline_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_baselines_project_id", "pep_baselines", ["project_id"])

    if not _has_table("pep_variations"):
        op.create_table(
            "pep_variations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("baseline_id", sa.Integer(), nullable=False),
            sa.Column("activity_id", sa.Integer(), nullable=True),
            sa.Column("original_value", sa.Numeric(15, 2), nullable=False),
            sa.Column("current_value", sa.Numeric(15, 2), nullable=False),
            sa.Column("variation_type", sa.String(length=32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["baseline_id"], ["pep_baselines.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["activity_id"], ["pep_activities.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_variations_baseline_id", "pep_variations", ["baseline_id"])

    # Decision & change logs, comments
    if not _has_table("pep_decision_logs"):
        op.create_table(
            "pep_decision_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("decision", sa.Text(), nullable=False),
            sa.Column("justification", sa.Text(), nullable=True),
            sa.Column("owner_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_decision_logs_project_id", "pep_decision_logs", ["project_id"])

    if not _has_table("pep_change_logs"):
        op.create_table(
            "pep_change_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("change_description", sa.Text(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_change_logs_project_id", "pep_change_logs", ["project_id"])

    if not _has_table("pep_comments"):
        op.create_table(
            "pep_comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pep_comments_entity", "pep_comments", ["entity_type", "entity_id"])


def downgrade():
    # Drop in reverse dependency order (best-effort).
    for name in [
        "pep_comments",
        "pep_change_logs",
        "pep_decision_logs",
        "pep_variations",
        "pep_baselines",
        "pep_resource_capacities",
        "pep_resource_allocations",
        "pep_risk_logs",
        "pep_risks",
        "pep_activity_logs",
        "pep_activities",
        "pep_stages",
        "pep_phases",
    ]:
        op.drop_table(name)

