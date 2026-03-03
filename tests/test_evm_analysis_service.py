"""Tests for EVMAnalysisService."""
import pytest
from datetime import date
from app.models.project import Project
from app.models.user import User
from app.models.financial_earned_value import FinancialEarnedValue
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
