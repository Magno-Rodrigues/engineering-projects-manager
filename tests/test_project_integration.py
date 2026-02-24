"""Tests for ProjectCharter and ProjectClosure model integration."""
from app.models.project_charter import ProjectCharter
from app.models.project_closure import ProjectClosure


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