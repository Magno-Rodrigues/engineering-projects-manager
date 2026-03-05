"""Tests for ProjectCharter, ProjectClosure model integration, and migrations."""
from app.models.project_charter import ProjectCharter
from app.models.project_closure import ProjectClosure


class TestMigrationChain:
    """Tests for Alembic migration chain integrity."""

    def test_single_migration_head(self, app):
        """Ensure the migration chain has exactly one head.

        Multiple heads cause 'flask db upgrade' to fail with
        'Multiple head revisions are present', which prevents the database
        from being set up and results in a 500 on every route.
        """
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config('migrations/alembic.ini')
        alembic_cfg.set_main_option('script_location', 'migrations')
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        heads = script_dir.get_heads()
        assert len(heads) == 1, (
            f"Expected exactly 1 migration head but found {len(heads)}: {heads}. "
            "Run 'flask db merge heads' to fix multiple heads."
        )


class TestProjectCharter:
    """Tests for ProjectCharter model."""

    def test_create_project_charter(self, app, db):
        """Test that a ProjectCharter instance can be created."""
        with app.app_context():
            charter = ProjectCharter(project_id=1, created_by=1)
            assert charter is not None

    def test_project_charter_repr(self, app, db):
        """Test the string representation of a project charter."""
        with app.app_context():
            charter = ProjectCharter(project_id=1, created_by=1)
            assert 'ProjectCharter' in repr(charter)


class TestProjectClosure:
    """Tests for ProjectClosure model."""

    def test_create_project_closure(self, app, db):
        """Test that a ProjectClosure instance can be created."""
        with app.app_context():
            closure = ProjectClosure(project_id=1, created_by=1)
            assert closure is not None

    def test_project_closure_repr(self, app, db):
        """Test the string representation of a project closure."""
        with app.app_context():
            closure = ProjectClosure(project_id=1, created_by=1)
            assert 'ProjectClosure' in repr(closure)