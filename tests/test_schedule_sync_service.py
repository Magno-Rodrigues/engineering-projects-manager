"""Tests for ScheduleSyncService and related schedule sync functionality."""
import pytest
from datetime import date
from app.models.project import Project
from app.models.user import User
from app.models.import_log import ImportLog
from app.models.schedule_sync import ScheduleImportRecord
from app.services.schedule_sync_service import ScheduleSyncService, build_suggestion, month_label


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_month_label_valid(self):
        assert month_label('2024-01') == 'Jan/2024'
        assert month_label('2024-12') == 'Dez/2024'
        assert month_label('2025-06') == 'Jun/2025'

    def test_month_label_invalid(self):
        result = month_label('bad-data')
        assert result == 'bad-data'

    def test_build_suggestion_no_delay(self):
        record = ScheduleImportRecord(task_name='Test', progress=50)
        assert build_suggestion(record, 0) is None

    def test_build_suggestion_low_progress(self):
        record = ScheduleImportRecord(task_name='Test Task', progress=10)
        suggestion = build_suggestion(record, 5)
        assert suggestion is not None
        assert '10%' in suggestion

    def test_build_suggestion_critical_delay(self):
        record = ScheduleImportRecord(task_name='Critical Task', progress=50)
        suggestion = build_suggestion(record, 20)
        assert suggestion is not None
        assert '20 dias' in suggestion


# ---------------------------------------------------------------------------
# ScheduleImportRecord model tests
# ---------------------------------------------------------------------------

class TestScheduleImportRecord:
    def test_variance_days_positive(self):
        """Delayed: actual_end > planned_end → positive variance."""
        record = ScheduleImportRecord(
            task_name='Task',
            planned_end=date(2025, 3, 1),
            actual_end=date(2025, 3, 15),
        )
        assert record.variance_days == 14

    def test_variance_days_negative(self):
        """Early: actual_end < planned_end → negative variance."""
        record = ScheduleImportRecord(
            task_name='Task',
            planned_end=date(2025, 3, 15),
            actual_end=date(2025, 3, 1),
        )
        assert record.variance_days == -14

    def test_variance_days_no_dates(self):
        record = ScheduleImportRecord(task_name='Task')
        assert record.variance_days == 0

    def test_schedule_status_atrasada(self):
        record = ScheduleImportRecord(
            task_name='Task',
            planned_end=date(2025, 3, 1),
            actual_end=date(2025, 3, 15),
        )
        assert record.schedule_status == 'atrasada'

    def test_schedule_status_adiantada(self):
        record = ScheduleImportRecord(
            task_name='Task',
            planned_end=date(2025, 3, 15),
            actual_end=date(2025, 3, 1),
        )
        assert record.schedule_status == 'adiantada'

    def test_schedule_status_no_prazo(self):
        record = ScheduleImportRecord(
            task_name='Task',
            planned_end=date(2025, 3, 15),
            actual_end=date(2025, 3, 15),
        )
        assert record.schedule_status == 'no_prazo'


# ---------------------------------------------------------------------------
# Integration tests for ScheduleSyncService
# ---------------------------------------------------------------------------

@pytest.fixture
def sync_setup(app, db):
    """Create user, project, import log, and schedule records for testing."""
    with app.app_context():
        user = User(username='sync_test_user', email='sync@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.flush()

        project = Project(name='Sync Test Project', owner_id=user.id, status='planning')
        db.session.add(project)
        db.session.flush()

        import_log = ImportLog(
            project_id=project.id,
            created_by=user.id,
            import_type='ms_project',
            file_name='test.xml',
            status='success',
            total_tasks_imported=2,
            total_items_imported=0,
        )
        db.session.add(import_log)
        db.session.flush()

        # Two non-summary records
        rec1 = ScheduleImportRecord(
            import_log_id=import_log.id,
            project_id=project.id,
            external_task_id='1',
            task_name='Task Alpha',
            planned_start=date(2025, 3, 1),
            planned_end=date(2025, 3, 10),
            actual_start=date(2025, 3, 1),
            actual_end=date(2025, 3, 15),
            duration_hours=40,
            progress=100,
            is_summary=False,
        )
        rec2 = ScheduleImportRecord(
            import_log_id=import_log.id,
            project_id=project.id,
            external_task_id='2',
            task_name='Task Beta',
            planned_start=date(2025, 4, 1),
            planned_end=date(2025, 4, 20),
            actual_start=date(2025, 4, 1),
            actual_end=date(2025, 4, 18),
            duration_hours=80,
            progress=75,
            is_summary=False,
        )
        db.session.add(rec1)
        db.session.add(rec2)
        db.session.commit()

        yield {
            'user_id': user.id,
            'project_id': project.id,
            'import_log_id': import_log.id,
        }

        # Cleanup: use expunge_all + direct delete to avoid cascade conflicts
        db.session.expunge_all()
        from app.models.pep import PEPPhase, PEPChangeLog
        PEPChangeLog.query.filter_by(project_id=project.id).delete()
        db.session.execute(
            db.text('DELETE FROM schedule_import_records WHERE project_id = :pid'),
            {'pid': project.id},
        )
        db.session.execute(
            db.text('DELETE FROM import_logs WHERE project_id = :pid'),
            {'pid': project.id},
        )
        for phase in PEPPhase.query.filter_by(project_id=project.id).all():
            db.session.delete(phase)
        db.session.flush()
        db.session.execute(
            db.text('DELETE FROM projects WHERE id = :pid'),
            {'pid': project.id},
        )
        db.session.execute(
            db.text('DELETE FROM users WHERE id = :uid'),
            {'uid': user.id},
        )
        db.session.commit()


class TestScheduleSyncService:
    def test_import_to_eap_creates_phase_and_activities(self, app, db, sync_setup):
        with app.app_context():
            summary, error = ScheduleSyncService.import_to_eap(
                project_id=sync_setup['project_id'],
                import_log_id=sync_setup['import_log_id'],
                created_by=sync_setup['user_id'],
            )
            assert error is None
            assert summary is not None
            assert summary['activities_created'] == 2
            assert 'phase_id' in summary
            assert 'stage_id' in summary

    def test_import_to_eap_invalid_log(self, app, db, sync_setup):
        with app.app_context():
            summary, error = ScheduleSyncService.import_to_eap(
                project_id=sync_setup['project_id'],
                import_log_id=99999,
                created_by=sync_setup['user_id'],
            )
            assert error is not None
            assert summary is None

    def test_get_alerts_returns_counts(self, app, db, sync_setup):
        with app.app_context():
            alert_data = ScheduleSyncService.get_alerts(sync_setup['project_id'])
            assert 'count_atrasadas' in alert_data
            assert 'count_no_prazo' in alert_data
            assert 'count_adiantadas' in alert_data
            # Task Alpha is delayed (actual_end > planned_end)
            assert alert_data['count_atrasadas'] >= 1
            # Task Beta is early (actual_end < planned_end)
            assert alert_data['count_adiantadas'] >= 1

    def test_get_alerts_empty_project(self, app, db):
        with app.app_context():
            alert_data = ScheduleSyncService.get_alerts(99999)
            assert alert_data['total'] == 0
            assert alert_data['count_atrasadas'] == 0

    def test_get_variance_analysis_calculates_spi(self, app, db, sync_setup):
        with app.app_context():
            analysis = ScheduleSyncService.get_variance_analysis(sync_setup['project_id'])
            assert analysis['total_tasks'] >= 1
            assert 'spi' in analysis
            assert 'tasks_by_severity' in analysis
            assert 'monthly_trend' in analysis

    def test_get_variance_analysis_empty_project(self, app, db):
        with app.app_context():
            analysis = ScheduleSyncService.get_variance_analysis(99999)
            assert analysis['total_tasks'] == 0
            assert analysis['spi'] is None

    def test_get_sync_history_empty(self, app, db):
        with app.app_context():
            # Non-existent activity
            history = ScheduleSyncService.get_sync_history(99999)
            assert history == []
