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
