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

    def test_import_data_replaces_previous_tasks(self, app, db, svc_project, svc_user):
        """A second import should replace tasks created by the first import."""
        from app.models.task import Task
        with app.app_context():
            # First import
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'first.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='first.xml',
                import_type='ms_project',
                data=data,
            )
            count_after_first = Task.query.filter_by(project_id=svc_project, source='import').count()
            assert count_after_first >= 1

            # Second import
            data2, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'second.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='second.xml',
                import_type='ms_project',
                data=data2,
            )
            count_after_second = Task.query.filter_by(project_id=svc_project, source='import').count()
            # Number of imported tasks should equal one import's worth, not accumulate
            assert count_after_second == count_after_first

    def test_import_data_sets_source_import_on_tasks(self, app, db, svc_project, svc_user):
        """Tasks created by import should have source='import'."""
        from app.models.task import Task
        with app.app_context():
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'src.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='src.xml',
                import_type='ms_project',
                data=data,
            )
            tasks = Task.query.filter_by(project_id=svc_project, source='import').all()
            assert len(tasks) >= 1

    def test_get_logs_report_no_filters(self, app, db, svc_project, svc_user):
        with app.app_context():
            logs = ImportService.get_logs_report()
            assert isinstance(logs, list)

    def test_get_logs_report_filter_by_user(self, app, db, svc_project, svc_user):
        with app.app_context():
            data, _ = ImportService.parse_file(
                MINIMAL_MS_XML.encode(), 'report.xml', 'ms_project'
            )
            ImportService.import_data(
                project_id=svc_project,
                created_by=svc_user,
                file_name='report.xml',
                import_type='ms_project',
                data=data,
            )
            logs = ImportService.get_logs_report(user_id=svc_user)
            assert all(l.created_by == svc_user for l in logs)

    def test_get_logs_report_filter_by_project(self, app, db, svc_project, svc_user):
        with app.app_context():
            logs = ImportService.get_logs_report(project_id=svc_project)
            assert all(l.project_id == svc_project for l in logs)

    def test_get_logs_report_filter_by_date(self, app, db, svc_project, svc_user):
        with app.app_context():
            from datetime import datetime, timezone, timedelta
            future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
            logs = ImportService.get_logs_report(end_date=future)
            assert isinstance(logs, list)

