"""Tests for WBSService."""
import pytest
from app.models.project import Project
from app.models.user import User
from app.models.wbs_item import WBSItem
from app.services.wbs_service import WBSService


@pytest.fixture(scope='module')
def wbs_user(db, app):
    with app.app_context():
        user = User(username='wbsuser_mod', email='wbsuser_mod@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def wbs_project(db, app, wbs_user):
    with app.app_context():
        project = Project(
            name='WBS Module Test Project',
            owner_id=wbs_user,
            status='planning',
        )
        db.session.add(project)
        db.session.commit()
        yield project.id


class TestWBSService:
    def test_create_wbs_item(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='wbs-root-1',
                title='Root',
                level=1,
            )
            assert error is None
            assert item is not None
            assert item.wbs_code == 'wbs-root-1'
            assert item.title == 'Root'

    def test_create_wbs_item_missing_code(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='',
                title='Root',
            )
            assert item is None
            assert error is not None

    def test_create_wbs_item_missing_title(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='wbs-no-title',
                title='',
            )
            assert item is None
            assert error is not None

    def test_get_project_wbs(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='wbs-get-test',
                title='Root',
                level=1,
            )
            items = WBSService.get_project_wbs(wbs_project)
            assert len(items) >= 1

    def test_bulk_create_wbs_items(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            items_data = [
                {'uid': 'A', 'wbs_code': 'bulk-1', 'title': 'Phase 1', 'level': 1, 'parent_uid': None},
                {'uid': 'B', 'wbs_code': 'bulk-1.1', 'title': 'Task 1.1', 'level': 2, 'parent_uid': 'A'},
            ]
            created = WBSService.bulk_create_wbs_items(wbs_project, wbs_user, items_data)
            assert len(created) == 2
            child = created[1]
            assert child.parent_id == created[0].id


class TestWBSService:
    def test_create_wbs_item(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='1',
                title='Root',
                level=1,
            )
            assert error is None
            assert item is not None
            assert item.wbs_code == '1'
            assert item.title == 'Root'

    def test_create_wbs_item_missing_code(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='',
                title='Root',
            )
            assert item is None
            assert error is not None

    def test_create_wbs_item_missing_title(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            item, error = WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='1',
                title='',
            )
            assert item is None
            assert error is not None

    def test_get_project_wbs(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            WBSService.create_wbs_item(
                project_id=wbs_project,
                created_by=wbs_user,
                wbs_code='1',
                title='Root',
                level=1,
            )
            items = WBSService.get_project_wbs(wbs_project)
            assert len(items) >= 1

    def test_bulk_create_wbs_items(self, app, db, wbs_project, wbs_user):
        with app.app_context():
            items_data = [
                {'uid': 'A', 'wbs_code': '1', 'title': 'Phase 1', 'level': 1, 'parent_uid': None},
                {'uid': 'B', 'wbs_code': '1.1', 'title': 'Task 1.1', 'level': 2, 'parent_uid': 'A'},
            ]
            created = WBSService.bulk_create_wbs_items(wbs_project, wbs_user, items_data)
            assert len(created) == 2
            child = created[1]
            assert child.parent_id == created[0].id
