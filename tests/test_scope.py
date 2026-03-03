"""Tests for PMBOK Scope Knowledge Area (Requirement, WBSItem, ScopeChange)."""
import pytest
from datetime import date
from app.models.requirement import Requirement
from app.models.wbs_item import WBSItem
from app.models.scope_change import ScopeChange
from app.models.project import Project
from app.models.user import User
from app.services.scope_service import ScopeService
from app import db as _db


@pytest.fixture(scope='function')
def scope_user(app, db):
    """Create a user for scope tests."""
    with app.app_context():
        user = User(username='scope_user', email='scope@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        db.session.delete(db.session.get(User, uid))
        db.session.commit()


@pytest.fixture(scope='function')
def scope_project(app, db, scope_user):
    """Create a project for scope tests."""
    with app.app_context():
        project = Project(name='Scope Project', owner_id=scope_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        db.session.delete(db.session.get(Project, pid))
        db.session.commit()


class TestRequirementModel:
    """Tests for Requirement model."""

    def test_requirement_repr(self, app, db, scope_project, scope_user):
        """Test requirement string representation."""
        with app.app_context():
            req = Requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-001',
                title='Sample Requirement',
            )
            assert 'Requirement' in repr(req)
            assert 'REQ-001' in repr(req)

    def test_requirement_default_status(self, app, db, scope_project, scope_user):
        """Test that new requirements default to draft status."""
        with app.app_context():
            req = Requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-002',
                title='Sample Requirement 2',
            )
            db.session.add(req)
            db.session.commit()
            assert req.status == 'draft'
            db.session.delete(req)
            db.session.commit()


class TestWBSItemModel:
    """Tests for WBSItem model."""

    def test_wbs_item_repr(self, app, db, scope_project, scope_user):
        """Test WBS item string representation."""
        with app.app_context():
            item = WBSItem(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='1.1',
                title='Design Phase',
            )
            assert 'WBSItem' in repr(item)
            assert '1.1' in repr(item)

    def test_wbs_item_default_status(self, app, db, scope_project, scope_user):
        """Test that new WBS items default to planning status."""
        with app.app_context():
            item = WBSItem(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='1.2',
                title='Development Phase',
            )
            db.session.add(item)
            db.session.commit()
            assert item.status == 'planning'
            db.session.delete(item)
            db.session.commit()


class TestScopeChangeModel:
    """Tests for ScopeChange model."""

    def test_scope_change_repr(self, app, db, scope_project, scope_user):
        """Test scope change string representation."""
        with app.app_context():
            change = ScopeChange(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-001',
                title='Add feature X',
            )
            assert 'ScopeChange' in repr(change)
            assert 'SC-001' in repr(change)

    def test_scope_change_default_status(self, app, db, scope_project, scope_user):
        """Test that new scope changes default to draft status."""
        with app.app_context():
            change = ScopeChange(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-002',
                title='Remove feature Y',
            )
            db.session.add(change)
            db.session.commit()
            assert change.status == 'draft'
            db.session.delete(change)
            db.session.commit()


class TestScopeService:
    """Tests for ScopeService."""

    # ---------------------------------------------------------------
    # Requirement tests
    # ---------------------------------------------------------------

    def test_create_requirement_success(self, app, db, scope_project, scope_user):
        """Test creating a requirement successfully."""
        with app.app_context():
            req, error = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-100',
                title='User authentication',
                category='functional',
                priority='high',
            )
            assert error is None
            assert req is not None
            assert req.status == 'draft'
            assert req.title == 'User authentication'
            db.session.delete(req)
            db.session.commit()

    def test_create_requirement_invalid_project(self, app, db, scope_user):
        """Test creating a requirement for a non-existent project."""
        with app.app_context():
            req, error = ScopeService.create_requirement(
                project_id=99999,
                created_by=scope_user,
                requirement_id='REQ-101',
                title='Some requirement',
            )
            assert req is None
            assert error is not None

    def test_create_requirement_missing_title(self, app, db, scope_project, scope_user):
        """Test that a missing title returns an error."""
        with app.app_context():
            req, error = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-102',
                title='',
            )
            assert req is None
            assert error is not None

    def test_create_requirement_invalid_category(self, app, db, scope_project, scope_user):
        """Test that an invalid category returns an error."""
        with app.app_context():
            req, error = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-103',
                title='Some requirement',
                category='invalid_category',
            )
            assert req is None
            assert error is not None

    def test_create_requirement_duplicate_id(self, app, db, scope_project, scope_user):
        """Test that a duplicate requirement ID returns an error."""
        with app.app_context():
            req, _ = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-DUP',
                title='First requirement',
            )
            dup, error = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-DUP',
                title='Duplicate requirement',
            )
            assert dup is None
            assert error is not None
            db.session.delete(req)
            db.session.commit()

    def test_approve_requirement(self, app, db, scope_project, scope_user):
        """Test approving a requirement."""
        with app.app_context():
            req, _ = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-200',
                title='Approve me',
            )
            approved, error = ScopeService.approve_requirement(req.id)
            assert error is None
            assert approved.status == 'approved'
            db.session.delete(approved)
            db.session.commit()

    def test_approve_nonexistent_requirement(self, app, db):
        """Test approving a non-existent requirement returns an error."""
        with app.app_context():
            req, error = ScopeService.approve_requirement(99999)
            assert req is None
            assert error is not None

    def test_approve_already_approved_requirement(self, app, db, scope_project, scope_user):
        """Test that approving an already-approved requirement returns an error."""
        with app.app_context():
            req, _ = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-201',
                title='Already approved',
            )
            ScopeService.approve_requirement(req.id)
            _, error = ScopeService.approve_requirement(req.id)
            assert error is not None
            db.session.delete(db.session.get(Requirement, req.id))
            db.session.commit()

    def test_get_project_requirements(self, app, db, scope_project, scope_user):
        """Test retrieving all requirements for a project."""
        with app.app_context():
            req, _ = ScopeService.create_requirement(
                project_id=scope_project,
                created_by=scope_user,
                requirement_id='REQ-300',
                title='List me',
            )
            requirements = ScopeService.get_project_requirements(scope_project)
            assert any(r.requirement_id == 'REQ-300' for r in requirements)
            db.session.delete(req)
            db.session.commit()

    # ---------------------------------------------------------------
    # WBS tests
    # ---------------------------------------------------------------

    def test_create_wbs_item_success(self, app, db, scope_project, scope_user):
        """Test creating a WBS item successfully."""
        with app.app_context():
            item, error = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='1',
                title='Project Management',
                level=1,
            )
            assert error is None
            assert item is not None
            assert item.status == 'planning'
            db.session.delete(item)
            db.session.commit()

    def test_create_wbs_item_invalid_project(self, app, db, scope_user):
        """Test creating a WBS item for a non-existent project."""
        with app.app_context():
            item, error = ScopeService.create_wbs_item(
                project_id=99999,
                created_by=scope_user,
                wbs_code='1',
                title='Some WBS item',
            )
            assert item is None
            assert error is not None

    def test_create_wbs_item_negative_effort(self, app, db, scope_project, scope_user):
        """Test that negative estimated effort returns an error."""
        with app.app_context():
            item, error = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='1.1',
                title='Some task',
                estimated_effort='-10',
            )
            assert item is None
            assert 'negative' in error.lower()

    def test_create_wbs_item_with_parent(self, app, db, scope_project, scope_user):
        """Test creating a child WBS item with a valid parent."""
        with app.app_context():
            parent, _ = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='2',
                title='Parent Item',
                level=1,
            )
            child, error = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='2.1',
                title='Child Item',
                level=2,
                parent_id=parent.id,
            )
            assert error is None
            assert child.parent_id == parent.id
            db.session.delete(child)
            db.session.delete(parent)
            db.session.commit()

    def test_calculate_wbs_effort(self, app, db, scope_project, scope_user):
        """Test calculating total WBS effort for a project."""
        with app.app_context():
            item1, _ = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='3',
                title='Task A',
                estimated_effort='10',
                actual_effort='8',
            )
            item2, _ = ScopeService.create_wbs_item(
                project_id=scope_project,
                created_by=scope_user,
                wbs_code='3.1',
                title='Task B',
                estimated_effort='5',
                actual_effort='6',
            )
            effort = ScopeService.calculate_wbs_effort(scope_project)
            assert effort['estimated_effort'] >= 15
            assert effort['actual_effort'] >= 14
            db.session.delete(item1)
            db.session.delete(item2)
            db.session.commit()

    # ---------------------------------------------------------------
    # Scope change tests
    # ---------------------------------------------------------------

    def test_create_scope_change_success(self, app, db, scope_project, scope_user):
        """Test creating a scope change successfully."""
        with app.app_context():
            change, error = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-100',
                title='Add reporting module',
                change_type='addition',
            )
            assert error is None
            assert change is not None
            assert change.status == 'draft'
            db.session.delete(change)
            db.session.commit()

    def test_create_scope_change_invalid_project(self, app, db, scope_user):
        """Test creating a scope change for a non-existent project."""
        with app.app_context():
            change, error = ScopeService.create_scope_change(
                project_id=99999,
                requested_by=scope_user,
                change_id='SC-101',
                title='Some change',
            )
            assert change is None
            assert error is not None

    def test_create_scope_change_invalid_type(self, app, db, scope_project, scope_user):
        """Test that an invalid change type returns an error."""
        with app.app_context():
            change, error = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-102',
                title='Some change',
                change_type='invalid_type',
            )
            assert change is None
            assert error is not None

    def test_create_scope_change_duplicate_id(self, app, db, scope_project, scope_user):
        """Test that a duplicate change ID returns an error."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-DUP',
                title='First change',
            )
            dup, error = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-DUP',
                title='Duplicate change',
            )
            assert dup is None
            assert error is not None
            db.session.delete(change)
            db.session.commit()

    def test_approve_scope_change(self, app, db, scope_project, scope_user):
        """Test approving a scope change."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-200',
                title='Approve me',
            )
            approved, error = ScopeService.approve_scope_change(
                scope_change_id=change.id,
                approved_by=scope_user,
                approved=True,
            )
            assert error is None
            assert approved.status == 'approved'
            assert approved.approved_by == scope_user
            db.session.delete(approved)
            db.session.commit()

    def test_reject_scope_change(self, app, db, scope_project, scope_user):
        """Test rejecting a scope change."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-201',
                title='Reject me',
            )
            rejected, error = ScopeService.approve_scope_change(
                scope_change_id=change.id,
                approved_by=scope_user,
                approved=False,
            )
            assert error is None
            assert rejected.status == 'rejected'
            db.session.delete(rejected)
            db.session.commit()

    def test_approve_nonexistent_scope_change(self, app, db, scope_user):
        """Test approving a non-existent scope change returns an error."""
        with app.app_context():
            change, error = ScopeService.approve_scope_change(
                scope_change_id=99999,
                approved_by=scope_user,
            )
            assert change is None
            assert error is not None

    def test_get_change_impact_analysis(self, app, db, scope_project, scope_user):
        """Test retrieving impact analysis for a scope change."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(
                project_id=scope_project,
                requested_by=scope_user,
                change_id='SC-300',
                title='Impact test',
                impact_analysis='This will affect module A and B.',
                affected_requirements=['REQ-001', 'REQ-002'],
            )
            analysis = ScopeService.get_change_impact_analysis(change.id)
            assert analysis is not None
            assert analysis['impact_analysis'] == 'This will affect module A and B.'
            assert 'REQ-001' in analysis['affected_requirements']
            db.session.delete(change)
            db.session.commit()

    def test_get_change_impact_analysis_not_found(self, app, db):
        """Test that get_change_impact_analysis returns None for missing change."""
        with app.app_context():
            result = ScopeService.get_change_impact_analysis(99999)
            assert result is None
