"""Tests for EVMAnalysisService."""
import pytest
from datetime import date, timedelta
from app.models.project import Project
from app.models.user import User
from app.models.financial_earned_value import FinancialEarnedValue
from app.models.task import Task
from app.services.evm_analysis_service import EVMAnalysisService


@pytest.fixture(scope='function')
def evm_user(app, db):
    with app.app_context():
        user = User(username='evm_user2', email='evm2@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        u = db.session.get(User, uid)
        if u:
            db.session.delete(u)
            db.session.commit()


@pytest.fixture(scope='function')
def evm_project(app, db, evm_user):
    with app.app_context():
        project = Project(name='EVM Analysis Project', owner_id=evm_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        p = db.session.get(Project, pid)
        if p:
            db.session.delete(p)
            db.session.commit()


class TestEVMAnalysisService:

    def test_get_scurve_data_empty(self, app, db, evm_project):
        with app.app_context():
            result = EVMAnalysisService.get_scurve_data(evm_project)
            assert result == []

    def test_get_scurve_data_with_reports(self, app, db, evm_project):
        with app.app_context():
            r = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 1, 31),
                bac=100000, ac=40000, ev=45000, pv=50000,
            )
            db.session.add(r)
            db.session.commit()
            result = EVMAnalysisService.get_scurve_data(evm_project)
            assert len(result) == 1
            assert result[0]['pv'] == 50000.0
            assert result[0]['ev'] == 45000.0
            assert result[0]['ac'] == 40000.0
            db.session.delete(r)
            db.session.commit()

    def test_get_evm_summary_no_data(self, app, db, evm_project):
        with app.app_context():
            result = EVMAnalysisService.get_evm_summary(evm_project)
            assert result is None

    def test_get_evm_summary_with_data(self, app, db, evm_project):
        with app.app_context():
            r = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 2, 29),
                bac=200000, ac=80000, ev=90000, pv=100000,
            )
            db.session.add(r)
            db.session.commit()
            result = EVMAnalysisService.get_evm_summary(evm_project)
            assert result is not None
            assert 'cpi' in result
            assert 'spi' in result
            assert result['cpi'] == pytest.approx(90000 / 80000)
            db.session.delete(r)
            db.session.commit()

    def test_get_performance_trend(self, app, db, evm_project):
        with app.app_context():
            r1 = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 1, 31),
                bac=100000, ac=40000, ev=45000, pv=50000,
            )
            r2 = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 2, 29),
                bac=100000, ac=75000, ev=80000, pv=85000,
            )
            db.session.add_all([r1, r2])
            db.session.commit()
            trend = EVMAnalysisService.get_performance_trend(evm_project)
            assert len(trend) == 2
            assert trend[0]['date'] < trend[1]['date']
            assert 'cpi' in trend[0]
            assert 'spi' in trend[0]
            db.session.delete(r1)
            db.session.delete(r2)
            db.session.commit()

    def test_get_variance_analysis_empty(self, app, db, evm_project):
        with app.app_context():
            result = EVMAnalysisService.get_variance_analysis(evm_project)
            assert result == []

    def test_get_variance_analysis_with_reports(self, app, db, evm_project):
        with app.app_context():
            r = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 3, 31),
                bac=100000, ac=60000, ev=70000, pv=80000,
            )
            db.session.add(r)
            db.session.commit()
            result = EVMAnalysisService.get_variance_analysis(evm_project)
            assert len(result) == 1
            row = result[0]
            assert row['date'] == '2024-03-31'
            # CV = EV - AC = 70000 - 60000 = 10000
            assert row['cost_variance'] == pytest.approx(10000.0)
            # SV = EV - PV = 70000 - 80000 = -10000
            assert row['schedule_variance'] == pytest.approx(-10000.0)
            assert row['cpi'] == pytest.approx(70000 / 60000)
            assert row['spi'] == pytest.approx(70000 / 80000)
            db.session.delete(r)
            db.session.commit()

    def test_get_variance_analysis_sorted_by_date(self, app, db, evm_project):
        with app.app_context():
            r1 = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 4, 30),
                bac=100000, ac=50000, ev=55000, pv=60000,
            )
            r2 = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 3, 31),
                bac=100000, ac=25000, ev=30000, pv=35000,
            )
            db.session.add_all([r1, r2])
            db.session.commit()
            result = EVMAnalysisService.get_variance_analysis(evm_project)
            assert len(result) == 2
            assert result[0]['date'] < result[1]['date']
            db.session.delete(r1)
            db.session.delete(r2)
            db.session.commit()

    def test_get_evm_summary_includes_eac_etc(self, app, db, evm_project):
        """EAC and ETC are auto-calculated when not provided."""
        with app.app_context():
            r = FinancialEarnedValue(
                project_id=evm_project, report_date=date(2024, 5, 31),
                bac=100000, ac=60000, ev=70000, pv=80000,
            )
            db.session.add(r)
            db.session.commit()
            result = EVMAnalysisService.get_evm_summary(evm_project)
            assert result is not None
            assert 'eac' in result
            assert 'etc' in result
            # EAC = BAC / CPI = 100000 / (70000/60000) ≈ 85714.29
            assert result['eac'] == pytest.approx(100000 / (70000 / 60000), rel=1e-3)
            # ETC = EAC - AC
            assert result['etc'] == pytest.approx(result['eac'] - 60000.0, rel=1e-3)
            db.session.delete(r)
            db.session.commit()

    # ------------------------------------------------------------------
    # get_schedule_comparison tests
    # ------------------------------------------------------------------

    def test_get_schedule_comparison_empty(self, app, db, evm_project):
        """Returns empty list when project has no tasks with planned dates."""
        with app.app_context():
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert result == []

    def test_get_schedule_comparison_task_not_started(self, app, db, evm_project):
        """Task whose start date is in the future has expected_progress == 0."""
        with app.app_context():
            future_start = date.today() + timedelta(days=10)
            future_end = date.today() + timedelta(days=20)
            task = Task(
                title='Future Task',
                project_id=evm_project,
                start_date=future_start,
                due_date=future_end,
                progress=0,
            )
            db.session.add(task)
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert len(result) == 1
            assert result[0]['expected_progress'] == 0.0
            assert result[0]['actual_progress'] == 0
            assert result[0]['variance'] == 0.0
            db.session.delete(task)
            db.session.commit()

    def test_get_schedule_comparison_task_overdue(self, app, db, evm_project):
        """Task past its due date has expected_progress == 100."""
        with app.app_context():
            past_start = date.today() - timedelta(days=20)
            past_end = date.today() - timedelta(days=5)
            task = Task(
                title='Overdue Task',
                project_id=evm_project,
                start_date=past_start,
                due_date=past_end,
                progress=80,
            )
            db.session.add(task)
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert len(result) == 1
            assert result[0]['expected_progress'] == 100.0
            assert result[0]['actual_progress'] == 80
            assert result[0]['variance'] == pytest.approx(-20.0)
            db.session.delete(task)
            db.session.commit()

    def test_get_schedule_comparison_in_progress(self, app, db, evm_project):
        """Task in progress: expected_progress interpolated between 0 and 100."""
        with app.app_context():
            # Place today exactly at the midpoint of a 10-day window
            start = date.today() - timedelta(days=5)
            end = date.today() + timedelta(days=5)
            task = Task(
                title='In-Progress Task',
                project_id=evm_project,
                start_date=start,
                due_date=end,
                progress=60,
            )
            db.session.add(task)
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert len(result) == 1
            row = result[0]
            assert row['expected_progress'] == pytest.approx(50.0)
            assert row['actual_progress'] == 60
            assert row['variance'] == pytest.approx(10.0)
            db.session.delete(task)
            db.session.commit()

    def test_get_schedule_comparison_excludes_tasks_without_dates(self, app, db, evm_project):
        """Tasks without start_date or due_date are excluded from results."""
        with app.app_context():
            task_no_dates = Task(
                title='No Dates Task',
                project_id=evm_project,
                progress=50,
            )
            db.session.add(task_no_dates)
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert all(r['title'] != 'No Dates Task' for r in result)
            db.session.delete(task_no_dates)
            db.session.commit()

    def test_get_schedule_comparison_skips_inverted_dates(self, app, db, evm_project):
        """Tasks with end <= start are silently skipped (invalid configuration)."""
        with app.app_context():
            task_inverted = Task(
                title='Inverted Dates Task',
                project_id=evm_project,
                start_date=date.today() + timedelta(days=5),
                due_date=date.today(),  # end before start
                progress=0,
            )
            db.session.add(task_inverted)
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            assert all(r['title'] != 'Inverted Dates Task' for r in result)
            db.session.delete(task_inverted)
            db.session.commit()

    def test_get_schedule_comparison_sorted_by_start_date(self, app, db, evm_project):
        """Results are sorted by start_date ascending."""
        with app.app_context():
            t1 = Task(
                title='Task B',
                project_id=evm_project,
                start_date=date.today() - timedelta(days=10),
                due_date=date.today() + timedelta(days=10),
                progress=30,
            )
            t2 = Task(
                title='Task A',
                project_id=evm_project,
                start_date=date.today() - timedelta(days=20),
                due_date=date.today() + timedelta(days=5),
                progress=70,
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            result = EVMAnalysisService.get_schedule_comparison(evm_project)
            # only include the two tasks we added (filter by title to avoid leakage)
            titles = [r['title'] for r in result if r['title'] in ('Task A', 'Task B')]
            assert titles == ['Task A', 'Task B']
            db.session.delete(t1)
            db.session.delete(t2)
            db.session.commit()
