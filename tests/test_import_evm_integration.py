"""End-to-end integration tests: schedule import → EVM reporting cycle.

Covers acceptance criteria from the functional-test issue:
- Upload and import schedule files (MS Project / Primavera)
- Data preview before confirmation
- S-curve generation after import
- Automatic EV, SPI, CPI calculations and indicators
- Baseline locking after import
- Planned-vs-actual comparison on the control dashboard
"""
import io
import pytest
from datetime import date
from decimal import Decimal

from app.models.project import Project
from app.models.user import User
from app.models.financial_budget import FinancialBudget
from app.models.financial_earned_value import FinancialEarnedValue
from app.models.task import Task
from app.services.import_service import ImportService
from app.services.evm_analysis_service import EVMAnalysisService

_MS_NS = 'http://schemas.microsoft.com/project'

# Minimal MS Project XML with two leaf tasks and baseline costs
MS_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="{_MS_NS}">
  <CurrencySymbol>BRL</CurrencySymbol>
  <Tasks>
    <Task>
      <UID>0</UID><Name>Summary</Name><WBS>0</WBS>
      <OutlineNumber>0</OutlineNumber><OutlineLevel>0</OutlineLevel>
      <Summary>1</Summary>
    </Task>
    <Task>
      <UID>1</UID><Name>Design</Name><WBS>1</WBS>
      <OutlineNumber>1</OutlineNumber><OutlineLevel>1</OutlineLevel>
      <Summary>0</Summary>
      <Start>2025-03-01T08:00:00</Start>
      <Finish>2025-03-10T17:00:00</Finish>
      <Duration>PT80H0M0S</Duration>
      <BaselineCost>10000.00</BaselineCost>
      <BaselineStart>2025-03-01T08:00:00</BaselineStart>
      <BaselineFinish>2025-03-10T17:00:00</BaselineFinish>
      <PercentComplete>100</PercentComplete>
    </Task>
    <Task>
      <UID>2</UID><Name>Development</Name><WBS>2</WBS>
      <OutlineNumber>2</OutlineNumber><OutlineLevel>1</OutlineLevel>
      <Summary>0</Summary>
      <Start>2025-03-11T08:00:00</Start>
      <Finish>2025-03-20T17:00:00</Finish>
      <Duration>PT80H0M0S</Duration>
      <BaselineCost>15000.00</BaselineCost>
      <BaselineStart>2025-03-11T08:00:00</BaselineStart>
      <BaselineFinish>2025-03-20T17:00:00</BaselineFinish>
      <PercentComplete>50</PercentComplete>
    </Task>
  </Tasks>
  <Resources/>
</Project>
""".encode()

# Minimal Primavera P6 XML with one activity
PRIMAVERA_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<APIBusinessObjects>
  <WBS ObjectId="10">
    <Code>PH1</Code>
    <Name>Phase 1</Name>
    <Level>1</Level>
  </WBS>
  <Activity ObjectId="100">
    <ActivityId>A1000</ActivityId>
    <Name>Site Preparation</Name>
    <WBSObjectId>10</WBSObjectId>
    <StartDate>2025-04-01T08:00:00</StartDate>
    <FinishDate>2025-04-10T17:00:00</FinishDate>
    <Duration>80</Duration>
    <BudgetedTotalCost>20000.00</BudgetedTotalCost>
  </Activity>
</APIBusinessObjects>
"""


@pytest.fixture(scope='module')
def int_user(db, app):
    with app.app_context():
        user = User(username='int_evm_user', email='int_evm@example.com', role='admin')
        user.set_password('integpass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def int_project(db, app, int_user):
    with app.app_context():
        project = Project(name='Import EVM Integration Project', owner_id=int_user, status='planning')
        db.session.add(project)
        db.session.commit()
        yield project.id


# ---------------------------------------------------------------------------
# 1. Import via ImportService (unit-level integration)
# ---------------------------------------------------------------------------

class TestImportCreatesTasksAndBudget:
    """Step 1 & 2: Import schedule files and verify tasks + budget are persisted."""

    def test_ms_project_import_creates_tasks(self, app, db, int_project, int_user):
        with app.app_context():
            data, errors = ImportService.parse_file(MS_XML, 'plan.xml', 'ms_project')
            assert errors == [], f'Unexpected parse errors: {errors}'
            log, err = ImportService.import_data(
                project_id=int_project,
                created_by=int_user,
                file_name='plan.xml',
                import_type='ms_project',
                data=data,
            )
            assert err is None
            assert log.status == 'success'
            assert log.total_tasks_imported == 2  # Design + Development
            tasks = Task.query.filter_by(project_id=int_project).all()
            names = {t.title for t in tasks}
            assert 'Design' in names
            assert 'Development' in names

    def test_ms_project_import_creates_budget_baseline(self, app, db, int_project, int_user):
        with app.app_context():
            data, _ = ImportService.parse_file(MS_XML, 'plan2.xml', 'ms_project')
            ImportService.import_data(
                project_id=int_project,
                created_by=int_user,
                file_name='plan2.xml',
                import_type='ms_project',
                data=data,
            )
            budgets = FinancialBudget.query.filter_by(project_id=int_project).all()
            assert len(budgets) >= 1
            # At least one budget has planned total matching baseline costs sum (25000)
            totals = [float(b.total_planned_budget) for b in budgets]
            assert any(t == pytest.approx(25000.0) for t in totals)

    def test_primavera_import_creates_task(self, app, db, int_project, int_user):
        with app.app_context():
            data, errors = ImportService.parse_file(PRIMAVERA_XML, 'p6.xml', 'primavera')
            assert errors == []
            log, err = ImportService.import_data(
                project_id=int_project,
                created_by=int_user,
                file_name='p6.xml',
                import_type='primavera',
                data=data,
            )
            assert err is None
            assert log.status == 'success'
            tasks = Task.query.filter_by(project_id=int_project).all()
            assert any(t.title == 'Site Preparation' for t in tasks)


# ---------------------------------------------------------------------------
# 2. Baseline locking (Step 5)
# ---------------------------------------------------------------------------

class TestBaselineLocking:
    """Confirming with lock_baseline=True must produce a locked, immutable budget."""

    def test_import_with_lock_baseline_creates_closed_budget(self, app, db, int_project, int_user):
        with app.app_context():
            data, _ = ImportService.parse_file(MS_XML, 'locked.xml', 'ms_project')
            log, err = ImportService.import_data(
                project_id=int_project,
                created_by=int_user,
                file_name='locked.xml',
                import_type='ms_project',
                data=data,
                lock_baseline=True,
            )
            assert err is None
            budget = (
                FinancialBudget.query
                .filter_by(project_id=int_project, status='closed')
                .order_by(FinancialBudget.id.desc())
                .first()
            )
            assert budget is not None
            assert budget.is_locked is True

    def test_import_without_lock_baseline_creates_active_budget(self, app, db, int_project, int_user):
        with app.app_context():
            data, _ = ImportService.parse_file(MS_XML, 'unlocked.xml', 'ms_project')
            ImportService.import_data(
                project_id=int_project,
                created_by=int_user,
                file_name='unlocked.xml',
                import_type='ms_project',
                data=data,
                lock_baseline=False,
            )
            budget = (
                FinancialBudget.query
                .filter_by(project_id=int_project, status='active')
                .order_by(FinancialBudget.id.desc())
                .first()
            )
            assert budget is not None
            assert budget.is_locked is False


# ---------------------------------------------------------------------------
# 3. S-curve and EVM calculations (Steps 3 & 4)
# ---------------------------------------------------------------------------

class TestSCurveAndEVMAfterImport:
    """After registering EVM reports for the imported project, verify S-curve,
    CPI, SPI and variance analysis outputs are correct."""

    @pytest.fixture(autouse=True)
    def _seed_evm_reports(self, app, db, int_project):
        """Seed two EVM data points for the integration project."""
        with app.app_context():
            r1 = FinancialEarnedValue(
                project_id=int_project,
                report_date=date(2025, 3, 15),
                bac=25000, ac=12000, ev=10000, pv=12500,
            )
            r2 = FinancialEarnedValue(
                project_id=int_project,
                report_date=date(2025, 3, 31),
                bac=25000, ac=22000, ev=21000, pv=25000,
            )
            db.session.add_all([r1, r2])
            db.session.commit()
            self._r1_id = r1.id
            self._r2_id = r2.id
        yield
        with app.app_context():
            for rid in (self._r1_id, self._r2_id):
                r = db.session.get(FinancialEarnedValue, rid)
                if r:
                    db.session.delete(r)
            db.session.commit()

    def test_scurve_data_has_two_points(self, app, db, int_project):
        with app.app_context():
            scurve = EVMAnalysisService.get_scurve_data(int_project)
            assert len(scurve) >= 2

    def test_scurve_data_sorted_by_date(self, app, db, int_project):
        with app.app_context():
            scurve = EVMAnalysisService.get_scurve_data(int_project)
            dates = [r['date'] for r in scurve]
            assert dates == sorted(dates)

    def test_scurve_contains_pv_ev_ac(self, app, db, int_project):
        with app.app_context():
            scurve = EVMAnalysisService.get_scurve_data(int_project)
            for point in scurve:
                assert 'pv' in point
                assert 'ev' in point
                assert 'ac' in point

    def test_evm_summary_cpi_and_spi(self, app, db, int_project):
        """Latest report: EV=21000, AC=22000, PV=25000 → CPI≈0.954, SPI=0.84."""
        with app.app_context():
            summary = EVMAnalysisService.get_evm_summary(int_project)
            assert summary is not None
            assert summary['cpi'] == pytest.approx(21000 / 22000, rel=1e-3)
            assert summary['spi'] == pytest.approx(21000 / 25000, rel=1e-3)

    def test_evm_summary_cost_variance_negative(self, app, db, int_project):
        """CV = EV - AC = 21000 - 22000 = -1000 (over budget)."""
        with app.app_context():
            summary = EVMAnalysisService.get_evm_summary(int_project)
            assert summary['cost_variance'] == pytest.approx(-1000.0)

    def test_evm_summary_schedule_variance_negative(self, app, db, int_project):
        """SV = EV - PV = 21000 - 25000 = -4000 (behind schedule)."""
        with app.app_context():
            summary = EVMAnalysisService.get_evm_summary(int_project)
            assert summary['schedule_variance'] == pytest.approx(-4000.0)

    def test_variance_analysis_includes_both_dates(self, app, db, int_project):
        with app.app_context():
            analysis = EVMAnalysisService.get_variance_analysis(int_project)
            assert len(analysis) >= 2
            for row in analysis:
                assert 'cost_variance' in row
                assert 'schedule_variance' in row
                assert 'cpi' in row
                assert 'spi' in row

    def test_variance_analysis_first_point_negative_cv(self, app, db, int_project):
        """First report: EV=10000, AC=12000 → CV=-2000 (over budget)."""
        with app.app_context():
            analysis = EVMAnalysisService.get_variance_analysis(int_project)
            first = next(r for r in analysis if r['date'] == '2025-03-15')
            assert first['cost_variance'] == pytest.approx(-2000.0)
            assert first['schedule_variance'] == pytest.approx(-2500.0)


# ---------------------------------------------------------------------------
# 4. Planned-vs-actual comparison dashboard (Step 6)
# ---------------------------------------------------------------------------

class TestComparisonDashboardRoute:
    """The comparison route must return 200 and expose planned/actual data."""

    @pytest.fixture()
    def logged_client(self, client, app, db, int_user):
        with app.app_context():
            user = db.session.get(User, int_user)
            username = user.username
        client.post('/login', data={'username': username, 'password': 'integpass'})
        return client

    def test_comparison_page_loads(self, logged_client, int_project):
        response = logged_client.get(f'/projects/{int_project}/financial/comparison')
        assert response.status_code == 200

    def test_comparison_page_contains_planned_and_actual_labels(self, logged_client, int_project):
        response = logged_client.get(f'/projects/{int_project}/financial/comparison')
        assert b'Planejado' in response.data
        assert b'Realizado' in response.data

    def test_evm_dashboard_page_loads(self, logged_client, int_project):
        response = logged_client.get(f'/projects/{int_project}/financial/evm-dashboard')
        assert response.status_code == 200
        assert b'EVM' in response.data
