"""Tests for PMBOK Integration Knowledge Area (ProjectCharter and ProjectClosure)."""
import pytest
from datetime import date
from app.models.project_charter import ProjectCharter
from app.models.project_closure import ProjectClosure
from app.models.project import Project
from app.models.user import User
from app.services.integration_service import ProjectIntegrationService
from app import db as _db


@pytest.fixture(scope='function')
def integration_user(app, db):
    """Create a user for integration tests."""
    with app.app_context():
        user = User(username='integration_user', email='integration@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        db.session.delete(db.session.get(User, uid))
        db.session.commit()


@pytest.fixture(scope='function')
def integration_project(app, db, integration_user):
    """Create a project for integration tests."""
    with app.app_context():
        project = Project(name='Integration Project', owner_id=integration_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        db.session.delete(db.session.get(Project, pid))
        db.session.commit()


class TestProjectCharterModel:
    """Tests for ProjectCharter model."""

    def test_charter_repr(self, app, db, integration_project, integration_user):
        """Test charter string representation."""
        with app.app_context():
            charter = ProjectCharter(project_id=integration_project, created_by=integration_user)
            assert 'ProjectCharter' in repr(charter)
            assert str(integration_project) in repr(charter)

    def test_charter_default_status(self, app, db, integration_project, integration_user):
        """Test that new charters default to draft status."""
        with app.app_context():
            charter = ProjectCharter(project_id=integration_project, created_by=integration_user)
            db.session.add(charter)
            db.session.commit()
            assert charter.status == 'draft'
            db.session.delete(charter)
            db.session.commit()


class TestProjectClosureModel:
    """Tests for ProjectClosure model."""

    def test_closure_repr(self, app, db, integration_project, integration_user):
        """Test closure string representation."""
        with app.app_context():
            closure = ProjectClosure(project_id=integration_project, created_by=integration_user)
            assert 'ProjectClosure' in repr(closure)
            assert str(integration_project) in repr(closure)

    def test_closure_default_status(self, app, db, integration_project, integration_user):
        """Test that new closures default to draft status."""
        with app.app_context():
            closure = ProjectClosure(project_id=integration_project, created_by=integration_user)
            db.session.add(closure)
            db.session.commit()
            assert closure.closure_status == 'draft'
            db.session.delete(closure)
            db.session.commit()


class TestProjectIntegrationService:
    """Tests for ProjectIntegrationService."""

    def test_create_charter_success(self, app, db, integration_project, integration_user):
        """Test creating a charter successfully."""
        with app.app_context():
            charter, error = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
                business_case='Business case text',
                project_purpose='Project purpose',
            )
            assert error is None
            assert charter is not None
            assert charter.status == 'draft'
            assert charter.business_case == 'Business case text'
            db.session.delete(charter)
            db.session.commit()

    def test_create_charter_invalid_project(self, app, db, integration_user):
        """Test creating a charter for a non-existent project."""
        with app.app_context():
            charter, error = ProjectIntegrationService.create_charter(
                project_id=99999,
                created_by=integration_user,
            )
            assert charter is None
            assert error is not None

    def test_create_charter_invalid_budget(self, app, db, integration_project, integration_user):
        """Test that a negative budget returns an error."""
        with app.app_context():
            charter, error = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
                approved_budget='-100',
            )
            assert charter is None
            assert 'negative' in error.lower()

    def test_create_charter_invalid_dates(self, app, db, integration_project, integration_user):
        """Test that end date before start date returns an error."""
        with app.app_context():
            charter, error = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
                scheduled_start_date=date(2025, 6, 1),
                scheduled_end_date=date(2025, 1, 1),
            )
            assert charter is None
            assert error is not None

    def test_get_charter_none_when_missing(self, app, db, integration_project):
        """Test that get_charter returns None when no charter exists."""
        with app.app_context():
            charter = ProjectIntegrationService.get_charter(integration_project)
            assert charter is None

    def test_approve_charter(self, app, db, integration_project, integration_user):
        """Test approving a charter."""
        with app.app_context():
            charter, _ = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
            )
            approved, error = ProjectIntegrationService.approve_charter(
                charter_id=charter.id,
                authorized_by=integration_user,
                approved=True,
            )
            assert error is None
            assert approved.status == 'approved'
            assert approved.authorized_by == integration_user
            db.session.delete(approved)
            db.session.commit()

    def test_reject_charter(self, app, db, integration_project, integration_user):
        """Test rejecting a charter."""
        with app.app_context():
            charter, _ = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
            )
            rejected, error = ProjectIntegrationService.approve_charter(
                charter_id=charter.id,
                authorized_by=integration_user,
                approved=False,
            )
            assert error is None
            assert rejected.status == 'rejected'
            db.session.delete(rejected)
            db.session.commit()

    def test_approve_nonexistent_charter(self, app, db, integration_user):
        """Test approving a non-existent charter returns an error."""
        with app.app_context():
            charter, error = ProjectIntegrationService.approve_charter(
                charter_id=99999,
                authorized_by=integration_user,
            )
            assert charter is None
            assert error is not None

    def test_approve_already_approved_charter(self, app, db, integration_project, integration_user):
        """Test that approving an already-approved charter returns an error."""
        with app.app_context():
            charter, _ = ProjectIntegrationService.create_charter(
                project_id=integration_project,
                created_by=integration_user,
            )
            ProjectIntegrationService.approve_charter(
                charter_id=charter.id, authorized_by=integration_user
            )
            _, error = ProjectIntegrationService.approve_charter(
                charter_id=charter.id, authorized_by=integration_user
            )
            assert error is not None
            db.session.delete(db.session.get(ProjectCharter, charter.id))
            db.session.commit()

    def test_create_closure_success(self, app, db, integration_project, integration_user):
        """Test creating a closure successfully."""
        with app.app_context():
            closure, error = ProjectIntegrationService.create_closure(
                project_id=integration_project,
                created_by=integration_user,
                lessons_learned='We learned a lot.',
                recommendations='Document everything.',
            )
            assert error is None
            assert closure is not None
            assert closure.closure_status == 'draft'
            assert closure.lessons_learned == 'We learned a lot.'
            db.session.delete(closure)
            db.session.commit()

    def test_create_closure_invalid_project(self, app, db, integration_user):
        """Test creating a closure for a non-existent project."""
        with app.app_context():
            closure, error = ProjectIntegrationService.create_closure(
                project_id=99999,
                created_by=integration_user,
            )
            assert closure is None
            assert error is not None

    def test_create_closure_invalid_cost(self, app, db, integration_project, integration_user):
        """Test that a negative actual final cost returns an error."""
        with app.app_context():
            closure, error = ProjectIntegrationService.create_closure(
                project_id=integration_project,
                created_by=integration_user,
                actual_final_cost='-500',
            )
            assert closure is None
            assert 'negative' in error.lower()

    def test_complete_project(self, app, db, integration_project, integration_user):
        """Test completing a project closure."""
        with app.app_context():
            closure, _ = ProjectIntegrationService.create_closure(
                project_id=integration_project,
                created_by=integration_user,
            )
            completed, error = ProjectIntegrationService.complete_project(
                closure_id=closure.id,
                approved_by=integration_user,
            )
            assert error is None
            assert completed.closure_status == 'completed'
            assert completed.approved_by == integration_user
            db.session.delete(completed)
            db.session.commit()

    def test_complete_nonexistent_closure(self, app, db, integration_user):
        """Test completing a non-existent closure returns an error."""
        with app.app_context():
            closure, error = ProjectIntegrationService.complete_project(
                closure_id=99999,
                approved_by=integration_user,
            )
            assert closure is None
            assert error is not None

    def test_get_lessons_learned(self, app, db, integration_project, integration_user):
        """Test retrieving lessons learned from a closure."""
        with app.app_context():
            closure, _ = ProjectIntegrationService.create_closure(
                project_id=integration_project,
                created_by=integration_user,
                lessons_learned='Key insight: plan early.',
            )
            lessons = ProjectIntegrationService.get_lessons_learned(integration_project)
            assert lessons == 'Key insight: plan early.'
            db.session.delete(closure)
            db.session.commit()

    def test_get_lessons_learned_no_closure(self, app, db, integration_project):
        """Test that get_lessons_learned returns None when no closure exists."""
        with app.app_context():
            lessons = ProjectIntegrationService.get_lessons_learned(integration_project)
            assert lessons is None
