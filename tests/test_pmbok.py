"""Tests for PMBOK Phase 1: Stakeholder and CommunicationPlan models and services."""
import pytest
from app import db
from app.models.stakeholder import Stakeholder
from app.models.communication_plan import CommunicationPlan
from app.models.project import Project
from app.models.user import User
from app.services.stakeholder_service import StakeholderService
from app.services.communication_plan_service import CommunicationPlanService


@pytest.fixture(scope='function')
def pmbok_user(app, db):
    """Create a user for PMBOK tests."""
    with app.app_context():
        user = User(username='pmbok_user', email='pmbok@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        db.session.delete(db.session.get(User, uid))
        db.session.commit()


@pytest.fixture(scope='function')
def pmbok_project(app, db, pmbok_user):
    """Create a project for PMBOK tests."""
    with app.app_context():
        project = Project(name='PMBOK Test Project', owner_id=pmbok_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        db.session.delete(db.session.get(Project, pid))
        db.session.commit()


class TestStakeholderModel:
    """Tests for Stakeholder model."""

    def test_stakeholder_repr(self, app, db, pmbok_project):
        """Test stakeholder string representation."""
        with app.app_context():
            s = Stakeholder(project_id=pmbok_project, name='Alice', interest_level='high', influence_level='medium', category='sponsor')
            assert 'Stakeholder' in repr(s)
            assert 'Alice' in repr(s)

    def test_stakeholder_defaults(self, app, db, pmbok_project):
        """Test that new stakeholders have default levels."""
        with app.app_context():
            s = Stakeholder(project_id=pmbok_project, name='Bob')
            db.session.add(s)
            db.session.commit()
            assert s.interest_level == 'medium'
            assert s.influence_level == 'medium'
            assert s.category == 'other'
            db.session.delete(s)
            db.session.commit()


class TestCommunicationPlanModel:
    """Tests for CommunicationPlan model."""

    def test_communication_plan_repr(self, app, db, pmbok_project, pmbok_user):
        """Test communication plan string representation."""
        with app.app_context():
            p = CommunicationPlan(project_id=pmbok_project, created_by=pmbok_user, information='Weekly status')
            assert 'CommunicationPlan' in repr(p)
            assert 'Weekly status' in repr(p)

    def test_communication_plan_defaults(self, app, db, pmbok_project, pmbok_user):
        """Test that new entries have default values."""
        with app.app_context():
            p = CommunicationPlan(project_id=pmbok_project, created_by=pmbok_user, information='Test info')
            db.session.add(p)
            db.session.commit()
            assert p.frequency == 'weekly'
            assert p.communication_method == 'email'
            assert p.distribution_method == 'direct'
            db.session.delete(p)
            db.session.commit()


class TestStakeholderService:
    """Tests for StakeholderService."""

    def test_create_stakeholder_success(self, app, db, pmbok_project):
        """Test creating a stakeholder successfully."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=pmbok_project,
                name='Carol',
                role='Project Sponsor',
                interest_level='high',
                influence_level='high',
                category='sponsor',
            )
            assert error is None
            assert s is not None
            assert s.name == 'Carol'
            assert s.category == 'sponsor'
            db.session.delete(s)
            db.session.commit()

    def test_create_stakeholder_invalid_project(self, app, db):
        """Test creating a stakeholder for a non-existent project."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=99999,
                name='Dave',
            )
            assert s is None
            assert 'not found' in error.lower()

    def test_create_stakeholder_missing_name(self, app, db, pmbok_project):
        """Test that missing name returns an error."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=pmbok_project,
                name='',
            )
            assert s is None
            assert error is not None

    def test_create_stakeholder_invalid_interest_level(self, app, db, pmbok_project):
        """Test that an invalid interest level returns an error."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=pmbok_project,
                name='Eve',
                interest_level='extreme',
            )
            assert s is None
            assert 'interest' in error.lower()

    def test_create_stakeholder_invalid_influence_level(self, app, db, pmbok_project):
        """Test that an invalid influence level returns an error."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=pmbok_project,
                name='Frank',
                influence_level='extreme',
            )
            assert s is None
            assert 'influence' in error.lower()

    def test_create_stakeholder_invalid_category(self, app, db, pmbok_project):
        """Test that an invalid category returns an error."""
        with app.app_context():
            s, error = StakeholderService.create_stakeholder(
                project_id=pmbok_project,
                name='Grace',
                category='unknown_cat',
            )
            assert s is None
            assert 'category' in error.lower()

    def test_get_project_stakeholders(self, app, db, pmbok_project):
        """Test listing stakeholders for a project."""
        with app.app_context():
            s1, _ = StakeholderService.create_stakeholder(project_id=pmbok_project, name='Hank')
            s2, _ = StakeholderService.create_stakeholder(project_id=pmbok_project, name='Ivy')
            stakeholders = StakeholderService.get_project_stakeholders(pmbok_project)
            names = [s.name for s in stakeholders]
            assert 'Hank' in names
            assert 'Ivy' in names
            db.session.delete(s1)
            db.session.delete(s2)
            db.session.commit()

    def test_delete_stakeholder_success(self, app, db, pmbok_project):
        """Test deleting a stakeholder successfully."""
        with app.app_context():
            s, _ = StakeholderService.create_stakeholder(project_id=pmbok_project, name='Jack')
            sid = s.id
            success, error = StakeholderService.delete_stakeholder(sid)
            assert success is True
            assert error is None
            assert db.session.get(Stakeholder, sid) is None

    def test_delete_stakeholder_not_found(self, app, db):
        """Test deleting a non-existent stakeholder returns an error."""
        with app.app_context():
            success, error = StakeholderService.delete_stakeholder(99999)
            assert success is False
            assert 'not found' in error.lower()


class TestCommunicationPlanService:
    """Tests for CommunicationPlanService."""

    def test_create_communication_plan_success(self, app, db, pmbok_project, pmbok_user):
        """Test creating a communication plan entry successfully."""
        with app.app_context():
            p, error = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project,
                created_by=pmbok_user,
                information='Weekly status report',
                frequency='weekly',
                responsible='PM',
                target_audience='Sponsor',
                communication_method='email',
                distribution_method='direct',
            )
            assert error is None
            assert p is not None
            assert p.information == 'Weekly status report'
            db.session.delete(p)
            db.session.commit()

    def test_create_communication_plan_invalid_project(self, app, db, pmbok_user):
        """Test creating a communication plan for a non-existent project."""
        with app.app_context():
            p, error = CommunicationPlanService.create_communication_plan(
                project_id=99999,
                created_by=pmbok_user,
                information='Test',
            )
            assert p is None
            assert 'not found' in error.lower()

    def test_create_communication_plan_missing_information(self, app, db, pmbok_project, pmbok_user):
        """Test that missing information returns an error."""
        with app.app_context():
            p, error = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project,
                created_by=pmbok_user,
                information='',
            )
            assert p is None
            assert error is not None

    def test_create_communication_plan_invalid_frequency(self, app, db, pmbok_project, pmbok_user):
        """Test that an invalid frequency returns an error."""
        with app.app_context():
            p, error = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project,
                created_by=pmbok_user,
                information='Test',
                frequency='hourly',
            )
            assert p is None
            assert 'frequency' in error.lower()

    def test_create_communication_plan_invalid_method(self, app, db, pmbok_project, pmbok_user):
        """Test that an invalid communication method returns an error."""
        with app.app_context():
            p, error = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project,
                created_by=pmbok_user,
                information='Test',
                communication_method='fax',
            )
            assert p is None
            assert 'method' in error.lower()

    def test_get_project_communication_plans(self, app, db, pmbok_project, pmbok_user):
        """Test listing communication plan entries for a project."""
        with app.app_context():
            p1, _ = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project, created_by=pmbok_user, information='Status A'
            )
            p2, _ = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project, created_by=pmbok_user, information='Status B'
            )
            plans = CommunicationPlanService.get_project_communication_plans(pmbok_project)
            infos = [p.information for p in plans]
            assert 'Status A' in infos
            assert 'Status B' in infos
            db.session.delete(p1)
            db.session.delete(p2)
            db.session.commit()

    def test_delete_communication_plan_success(self, app, db, pmbok_project, pmbok_user):
        """Test deleting a communication plan entry successfully."""
        with app.app_context():
            p, _ = CommunicationPlanService.create_communication_plan(
                project_id=pmbok_project, created_by=pmbok_user, information='To delete'
            )
            pid = p.id
            success, error = CommunicationPlanService.delete_communication_plan(pid)
            assert success is True
            assert error is None
            assert db.session.get(CommunicationPlan, pid) is None

    def test_delete_communication_plan_not_found(self, app, db):
        """Test deleting a non-existent communication plan entry returns an error."""
        with app.app_context():
            success, error = CommunicationPlanService.delete_communication_plan(99999)
            assert success is False
            assert 'not found' in error.lower()
