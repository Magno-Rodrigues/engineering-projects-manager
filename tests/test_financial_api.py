"""Tests for the financial REST API."""
import pytest
import json
from datetime import date
from app import db as _db
from app.models.project import Project
from app.models.user import User
from app.models.financial_transaction import FinancialTransaction


@pytest.fixture(scope='function')
def api_user(app, db):
    with app.app_context():
        user = User(username='api_user', email='api@example.com', role='admin')
        user.set_password('apipass')
        _db.session.add(user)
        _db.session.commit()
        yield user
        u = _db.session.get(User, user.id)
        if u:
            _db.session.delete(u)
            _db.session.commit()


@pytest.fixture(scope='function')
def api_project(app, db, api_user):
    # api_user with app.app_context(): is still active here, no need for another
    project = Project(name='API Test Project', owner_id=api_user.id)
    _db.session.add(project)
    _db.session.commit()
    pid = project.id
    yield pid
    p = _db.session.get(Project, pid)
    if p:
        _db.session.delete(p)
        _db.session.commit()


@pytest.fixture(scope='function')
def logged_in_client(app, db, api_user):
    with app.test_client() as client:
        client.post('/login', data={'username': api_user.username, 'password': 'apipass'})
        yield client


class TestFinancialAPI:

    def test_get_summary_unauthenticated(self, client):
        response = client.get('/api/projects/99999/financial/summary')
        assert response.status_code in (401, 302)

    def test_get_summary_authenticated(self, logged_in_client, api_project):
        response = logged_in_client.get(f'/api/projects/{api_project}/financial/summary')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data

    def test_get_transactions_authenticated(self, logged_in_client, api_project):
        response = logged_in_client.get(f'/api/projects/{api_project}/financial/transactions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data

    def test_create_transaction_authenticated(self, app, db, logged_in_client, api_project):
        payload = {
            'type': 'expense',
            'description': 'API Test Transaction',
            'amount': '500.00',
            'category': 'labor',
            'transaction_date': '2024-05-01',
        }
        response = logged_in_client.post(
            f'/api/projects/{api_project}/financial/transactions',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        with app.app_context():
            txn = _db.session.get(FinancialTransaction, data['id'])
            if txn:
                _db.session.delete(txn)
                _db.session.commit()

    def test_create_transaction_invalid_data(self, logged_in_client, api_project):
        payload = {'type': 'expense'}  # missing required fields
        response = logged_in_client.post(
            f'/api/projects/{api_project}/financial/transactions',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_update_transaction(self, app, db, logged_in_client, api_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=api_project, type='expense', description='To Update',
                amount=1000, category='labor', transaction_date=date(2024, 5, 10),
                payment_status='pending',
            )
            _db.session.add(t)
            _db.session.commit()
            tid = t.id
        payload = {'description': 'Updated Description', 'amount': '1500.00'}
        response = logged_in_client.put(
            f'/api/projects/{api_project}/financial/transactions/{tid}',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 200
        with app.app_context():
            t = _db.session.get(FinancialTransaction, tid)
            if t:
                _db.session.delete(t)
                _db.session.commit()

    def test_delete_transaction_api(self, app, db, logged_in_client, api_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=api_project, type='expense', description='To Delete',
                amount=200, category='other', transaction_date=date(2024, 5, 15),
                payment_status='pending',
            )
            _db.session.add(t)
            _db.session.commit()
            tid = t.id
        response = logged_in_client.delete(f'/api/projects/{api_project}/financial/transactions/{tid}')
        assert response.status_code == 200

    def test_get_cash_flow_api(self, logged_in_client, api_project):
        response = logged_in_client.get(f'/api/projects/{api_project}/financial/cash-flow')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cash_flow' in data

    def test_get_evm_api(self, logged_in_client, api_project):
        response = logged_in_client.get(f'/api/projects/{api_project}/financial/evm')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'evm_summary' in data

    def test_get_reports_api(self, logged_in_client, api_project):
        response = logged_in_client.get(f'/api/projects/{api_project}/financial/reports')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reports' in data

    def test_create_report_api(self, app, db, logged_in_client, api_project):
        payload = {'report_type': 'executive'}
        response = logged_in_client.post(
            f'/api/projects/{api_project}/financial/reports',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['report_type'] == 'executive'
        with app.app_context():
            from app.services.reporting_service import ReportingService
            ReportingService.delete_report(data['id'])

