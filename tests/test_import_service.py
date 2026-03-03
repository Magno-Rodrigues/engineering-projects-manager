"""Tests for ImportService."""
import pytest
from app.models.project import Project
from app.models.user import User
from app.models.import_log import ImportLog
from app.services.import_service import ImportService

_MS_NS = 'http://schemas.microsoft.com/project'

MINIMAL_MS_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="{_MS_NS}">
  <CurrencySymbol>BRL</CurrencySymbol>
  <Tasks>
    <Task>
      <UID>0</UID>
      <Name>Summary</Name>
      <WBS>0</WBS>
      <OutlineNumber>0</OutlineNumber>
      <OutlineLevel>0</OutlineLevel>
      <Summary>1</Summary>
    </Task>
    <Task>
      <UID>1</UID>
      <Name>Task Alpha</Name>
      <WBS>1</WBS>
      <OutlineNumber>1</OutlineNumber>
      <OutlineLevel>1</OutlineLevel>
      <Summary>0</Summary>
      <Start>2025-03-01T08:00:00</Start>
      <Finish>2025-03-05T17:00:00</Finish>
      <Duration>PT40H0M0S</Duration>
      <BaselineCost>2000.00</BaselineCost>
      <BaselineStart>2025-03-01T08:00:00</BaselineStart>
      <BaselineFinish>2025-03-05T17:00:00</BaselineFinish>
      <PercentComplete>0</PercentComplete>
    </Task>
  </Tasks>
  <Resources/>
</Project>
"""


@pytest.fixture(scope='module')
def svc_user(db, app):
    with app.app_context():
        user = User(username='svcuser_mod', email='svcuser_mod@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def svc_project(db, app, svc_user):
    with app.app_context():
        project = Project(name='Svc Module Test Project', owner_id=svc_user, status='planning')
        db.session.add(project)
        db.session.commit()
        yield project.id


class TestImportService:
    def test_parse_file_ms_project(self):
        data, errors = ImportService.parse_file(
            MINIMAL_MS_XML.encode(), 'plan.xml', 'ms_project'
        )
        assert errors == []
        assert data is not None
        assert len(data['tasks']) == 1

    def test_parse_file_unknown_type(self):
        data, errors = ImportService.parse_file(b'', 'plan.xml', 'unknown')
        assert data is None
        assert len(errors) > 0

    def test_import_data_creates_log(self, app, db, svc_project, svc_user):
        with app.app_context():
            data, errors = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'plan.xml', 'ms_project'
            )
            assert errors == []
            log, error = ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='plan.xml',
                import_type='ms_project',
                data=data,
            )
            assert error is None
            assert log is not None
            assert log.status == 'success'
            assert log.total_tasks_imported == 1

    def test_import_data_creates_task(self, app, db, svc_project, svc_user):
        from app.models.task import Task
        with app.app_context():
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'plan.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='plan.xml',
                import_type='ms_project',
                data=data,
            )
            tasks = Task.query.filter_by(project_id=svc_project).all()
            assert any(t.title == 'Task Alpha' for t in tasks)

    def test_get_import_logs(self, app, db, svc_project, svc_user):
        with app.app_context():
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'log_test.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='log_test.xml',
                import_type='ms_project',
                data=data,
            )
            logs = ImportService.get_import_logs(svc_project)
            assert any(l.file_name == 'log_test.xml' for l in logs)

    def test_rollback_import(self, app, db, svc_project, svc_user):
        with app.app_context():
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'rb.xml', 'ms_project'
            )
            log, _ = ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='rb.xml',
                import_type='ms_project',
                data=data,
            )
            assert log.status == 'success'
            ok, err = ImportService.rollback_import(log.id)
            assert ok is True
            assert err is None
            refreshed = db.session.get(ImportLog, log.id)
            assert refreshed.status == 'failed'

    def test_rollback_nonexistent(self, app, db):
        with app.app_context():
            ok, err = ImportService.rollback_import(999999)
            assert ok is False
            assert err is not None

    def test_rollback_failed_import(self, app, db, svc_project, svc_user):
        with app.app_context():
            log = ImportLog(
                project_id=svc_project,
                created_by=svc_user,
                import_type='ms_project',
                file_name='fail.xml',
                status='failed',
            )
            db.session.add(log)
            db.session.commit()
            ok, err = ImportService.rollback_import(log.id)
            assert ok is False
            assert err is not None
