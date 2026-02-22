"""Tests for task functionality."""
import pytest
from app.models.task import Task


class TestTaskModel:
    """Tests for Task model."""

    def test_task_default_status(self, app, db):
        """Test that task default status is 'todo'."""
        with app.app_context():
            task = Task(title='Test Task', project_id=1)
            assert task.status == 'todo'

    def test_task_default_priority(self, app, db):
        """Test that task default priority is 'medium'."""
        with app.app_context():
            task = Task(title='Test Task', project_id=1)
            assert task.priority == 'medium'

    def test_task_repr(self, app, db):
        """Test task string representation."""
        with app.app_context():
            task = Task(title='My Task', project_id=1)
            assert 'My Task' in repr(task)
