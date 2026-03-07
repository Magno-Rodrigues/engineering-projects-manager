"""Add ondelete=CASCADE to all ForeignKey constraints referencing projects.id

Revision ID: h1i2j3k4l5m6
Revises: g1h2i3j4k5l6
Create Date: 2026-03-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h1i2j3k4l5m6'
down_revision = 'g1h2i3j4k5l6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('communication_plans', schema=None) as batch_op:
        batch_op.drop_constraint('communication_plans_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'communication_plans_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('project_charters', schema=None) as batch_op:
        batch_op.drop_constraint('project_charters_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'project_charters_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('project_closures', schema=None) as batch_op:
        batch_op.drop_constraint('project_closures_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'project_closures_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_constraint('reports_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'reports_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('requirements', schema=None) as batch_op:
        batch_op.drop_constraint('requirements_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'requirements_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('scope_changes', schema=None) as batch_op:
        batch_op.drop_constraint('scope_changes_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'scope_changes_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('stakeholders', schema=None) as batch_op:
        batch_op.drop_constraint('stakeholders_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'stakeholders_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('tasks_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'tasks_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('time_entries', schema=None) as batch_op:
        batch_op.drop_constraint('time_entries_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'time_entries_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('wbs_items', schema=None) as batch_op:
        batch_op.drop_constraint('wbs_items_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'wbs_items_project_id_fkey', 'projects', ['project_id'], ['id'], ondelete='CASCADE'
        )


def downgrade():
    with op.batch_alter_table('wbs_items', schema=None) as batch_op:
        batch_op.drop_constraint('wbs_items_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'wbs_items_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('time_entries', schema=None) as batch_op:
        batch_op.drop_constraint('time_entries_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'time_entries_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('tasks_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'tasks_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('stakeholders', schema=None) as batch_op:
        batch_op.drop_constraint('stakeholders_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'stakeholders_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('scope_changes', schema=None) as batch_op:
        batch_op.drop_constraint('scope_changes_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'scope_changes_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('requirements', schema=None) as batch_op:
        batch_op.drop_constraint('requirements_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'requirements_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_constraint('reports_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'reports_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('project_closures', schema=None) as batch_op:
        batch_op.drop_constraint('project_closures_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'project_closures_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('project_charters', schema=None) as batch_op:
        batch_op.drop_constraint('project_charters_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'project_charters_project_id_fkey', 'projects', ['project_id'], ['id']
        )

    with op.batch_alter_table('communication_plans', schema=None) as batch_op:
        batch_op.drop_constraint('communication_plans_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'communication_plans_project_id_fkey', 'projects', ['project_id'], ['id']
        )
