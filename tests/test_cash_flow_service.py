"""Tests for CashFlowService."""
import pytest
from datetime import date
from app.models.project import Project
from app.models.user import User
from app.models.financial_transaction import FinancialTransaction
from app.services.cash_flow_service import CashFlowService


@pytest.fixture(scope='function')
def cf_user(app, db):
    with app.app_context():
        user = User(username='cf_user', email='cf@example.com')
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
def cf_project(app, db, cf_user):
    with app.app_context():
        project = Project(name='CF Test Project', owner_id=cf_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        p = db.session.get(Project, pid)
        if p:
            db.session.delete(p)
            db.session.commit()


class TestCashFlowService:

    def test_get_monthly_cash_flow_empty(self, app, db, cf_project):
        with app.app_context():
            result = CashFlowService.get_monthly_cash_flow(cf_project)
            assert result == []

    def test_get_monthly_cash_flow_with_data(self, app, db, cf_project):
        with app.app_context():
            t1 = FinancialTransaction(
                project_id=cf_project, type='expense', description='Test',
                amount=1000, category='labor', transaction_date=date(2024, 1, 15),
                payment_status='completed',
            )
            t2 = FinancialTransaction(
                project_id=cf_project, type='revenue', description='Income',
                amount=2000, category='service', transaction_date=date(2024, 1, 20),
                payment_status='completed',
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            result = CashFlowService.get_monthly_cash_flow(cf_project)
            assert len(result) == 1
            assert result[0]['month'] == '2024-01'
            assert result[0]['inflows'] == 2000.0
            assert result[0]['outflows'] == 1000.0
            assert result[0]['net_cash_flow'] == 1000.0
            db.session.delete(t1)
            db.session.delete(t2)
            db.session.commit()

    def test_get_cash_flow_projection(self, app, db, cf_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=cf_project, type='revenue', description='Rev',
                amount=3000, category='service', transaction_date=date(2024, 3, 10),
                payment_status='completed',
            )
            db.session.add(t)
            db.session.commit()
            result = CashFlowService.get_cash_flow_projection(cf_project, months_ahead=2)
            assert len(result) == 2
            assert result[0]['projected'] is True
            db.session.delete(t)
            db.session.commit()

    def test_get_cash_flow_projection_empty(self, app, db, cf_project):
        with app.app_context():
            result = CashFlowService.get_cash_flow_projection(cf_project, months_ahead=3)
            assert result == []

    def test_get_seasonal_analysis(self, app, db, cf_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=cf_project, type='expense', description='Seasonal',
                amount=500, category='material', transaction_date=date(2024, 6, 5),
                payment_status='completed',
            )
            db.session.add(t)
            db.session.commit()
            result = CashFlowService.get_seasonal_analysis(cf_project)
            assert len(result) == 12
            june = next(r for r in result if r['month_number'] == 6)
            assert june['avg_outflows'] == 500.0
            db.session.delete(t)
            db.session.commit()

    def test_simulate_scenario(self, app, db, cf_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=cf_project, type='expense', description='Simulate',
                amount=1000, category='labor', transaction_date=date(2024, 4, 1),
                payment_status='completed',
            )
            db.session.add(t)
            db.session.commit()
            result = CashFlowService.simulate_scenario(cf_project, 10.0, 0.0)
            assert len(result) == 1
            assert result[0]['outflows'] == pytest.approx(1100.0)
            db.session.delete(t)
            db.session.commit()
