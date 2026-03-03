"""Tests for new financial web routes."""
import pytest
from app import db as _db
from app.models.project import Project
from app.models.user import User


@pytest.fixture(scope='function')
def route_user(app, db):
    with app.app_context():
        user = User(username='route_user', email='route@example.com', role='admin')
        user.set_password('routepass')
        _db.session.add(user)
        _db.session.commit()
        yield user
        u = _db.session.get(User, user.id)
        if u:
            _db.session.delete(u)
            _db.session.commit()


@pytest.fixture(scope='function')
def route_project(app, db, route_user):
    # route_user's with app.app_context(): is still active here, no need for another
    project = Project(name='Route Test Project', owner_id=route_user.id)
    _db.session.add(project)
    _db.session.commit()
    pid = project.id
    yield pid
    p = _db.session.get(Project, pid)
    if p:
        _db.session.delete(p)
        _db.session.commit()


@pytest.fixture(scope='function')
def logged_in_client(app, db, route_user):
    with app.test_client() as client:
        client.post('/login', data={'username': route_user.username, 'password': 'routepass'})
        yield client


class TestFinancialRoutes:

    def test_cash_flow_route(self, logged_in_client, route_project):
        response = logged_in_client.get(f'/projects/{route_project}/financial/cash-flow')
        assert response.status_code == 200
        assert b'Fluxo de Caixa' in response.data

    def test_comparison_route(self, logged_in_client, route_project):
        response = logged_in_client.get(f'/projects/{route_project}/financial/comparison')
        assert response.status_code == 200
        assert b'Comparativo' in response.data

    def test_evm_dashboard_route(self, logged_in_client, route_project):
        response = logged_in_client.get(f'/projects/{route_project}/financial/evm-dashboard')
        assert response.status_code == 200
        assert b'EVM' in response.data

    def test_reports_route(self, logged_in_client, route_project):
        response = logged_in_client.get(f'/projects/{route_project}/financial/reports')
        assert response.status_code == 200
        assert b'Relat' in response.data
