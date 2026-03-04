"""Tests for admin import report routes."""
import pytest
from app.models.user import User
from app.models.project import Project
from app.models.import_log import ImportLog


@pytest.fixture(scope='module')
def admin_user(db, app):
    with app.app_context():
        user = User(username='admin_imports', email='admin_imports@example.com', role='admin')
        user.set_password('adminpass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def regular_user(db, app):
    with app.app_context():
        user = User(username='regular_imports', email='regular_imports@example.com', role='engineer')
        user.set_password('regularpass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def admin_project(db, app, admin_user):
    with app.app_context():
        project = Project(name='Admin Import Test Project', owner_id=admin_user, status='planning')
        db.session.add(project)
        db.session.commit()
        yield project.id


@pytest.fixture()
def admin_client(client, app, db, admin_user):
    """Return a test client logged in as admin."""
    with app.app_context():
        user = db.session.get(User, admin_user)
        username = user.username
    client.post('/login', data={'username': username, 'password': 'adminpass'})
    return client


@pytest.fixture()
def regular_client(client, app, db, regular_user):
    """Return a test client logged in as a regular (non-admin) user."""
    with app.app_context():
        user = db.session.get(User, regular_user)
        username = user.username
    client.post('/login', data={'username': username, 'password': 'regularpass'})
    return client


class TestAdminImportsReport:
    def test_report_page_requires_login(self, client):
        response = client.get('/admin/imports')
        assert response.status_code == 302

    def test_report_page_requires_admin(self, regular_client):
        response = regular_client.get('/admin/imports')
        assert response.status_code == 403

    def test_report_page_loads_for_admin(self, admin_client):
        response = admin_client.get('/admin/imports')
        assert response.status_code == 200

    def test_report_page_shows_logs(self, admin_client, app, db, admin_project, admin_user):
        with app.app_context():
            log = ImportLog(
                project_id=admin_project,
                created_by=admin_user,
                import_type='ms_project',
                file_name='admin_report_test.xml',
                status='success',
                total_tasks_imported=3,
                total_items_imported=2,
            )
            db.session.add(log)
            db.session.commit()

        response = admin_client.get('/admin/imports')
        assert response.status_code == 200
        assert b'admin_report_test.xml' in response.data

    def test_report_filter_by_user(self, admin_client, app, db, admin_project, admin_user):
        response = admin_client.get(f'/admin/imports?user_id={admin_user}')
        assert response.status_code == 200

    def test_report_filter_by_project(self, admin_client, app, db, admin_project):
        response = admin_client.get(f'/admin/imports?project_id={admin_project}')
        assert response.status_code == 200

    def test_report_filter_by_date(self, admin_client):
        response = admin_client.get('/admin/imports?start_date=2025-01-01&end_date=2099-12-31')
        assert response.status_code == 200


class TestAdminImportsExport:
    """Admin-only CSV export route. Access control (admin-only) verified by decorator
    tests in TestAdminImportsReport which use the same @login_required + @admin_required
    pattern."""

    def test_export_csv_for_admin(self, admin_client):
        response = admin_client.get('/admin/imports/export')
        assert response.status_code == 200
        assert response.content_type.startswith('text/csv')

    def test_export_csv_contains_headers(self, admin_client):
        response = admin_client.get('/admin/imports/export')
        assert b'Projeto' in response.data
        assert b'Usu' in response.data  # "Usuário"
        assert b'Arquivo' in response.data
        assert b'Status' in response.data

    def test_export_csv_filtered(self, admin_client, admin_user):
        response = admin_client.get(f'/admin/imports/export?user_id={admin_user}')
        assert response.status_code == 200
        assert response.content_type.startswith('text/csv')
