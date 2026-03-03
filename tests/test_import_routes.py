"""Functional tests for import web routes (upload, preview, baseline locking)."""
import io
import pytest
from app.models.user import User
from app.models.project import Project
from app.models.import_log import ImportLog
from app.models.financial_budget import FinancialBudget

_MS_NS = 'http://schemas.microsoft.com/project'

MINIMAL_MS_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="{_MS_NS}">
  <CurrencySymbol>BRL</CurrencySymbol>
  <Tasks>
    <Task>
      <UID>0</UID><Name>Summary</Name><WBS>0</WBS>
      <OutlineNumber>0</OutlineNumber><OutlineLevel>0</OutlineLevel>
      <Summary>1</Summary>
    </Task>
    <Task>
      <UID>1</UID><Name>Task Alpha</Name><WBS>1</WBS>
      <OutlineNumber>1</OutlineNumber><OutlineLevel>1</OutlineLevel>
      <Summary>0</Summary>
      <Start>2025-03-01T08:00:00</Start>
      <Finish>2025-03-05T17:00:00</Finish>
      <Duration>PT40H0M0S</Duration>
      <BaselineCost>5000.00</BaselineCost>
      <BaselineStart>2025-03-01T08:00:00</BaselineStart>
      <BaselineFinish>2025-03-05T17:00:00</BaselineFinish>
      <PercentComplete>0</PercentComplete>
    </Task>
  </Tasks>
  <Resources/>
</Project>
""".encode()


@pytest.fixture(scope='module')
def route_user(db, app):
    with app.app_context():
        user = User(username='routeuser', email='routeuser@example.com', role='admin')
        user.set_password('routepass')
        db.session.add(user)
        db.session.commit()
        yield user.id


@pytest.fixture(scope='module')
def route_project(db, app, route_user):
    with app.app_context():
        project = Project(name='Route Test Project', owner_id=route_user, status='planning')
        db.session.add(project)
        db.session.commit()
        yield project.id


@pytest.fixture()
def logged_client(client, app, db, route_user):
    """Return a test client logged in as the route_user."""
    with app.app_context():
        user = db.session.get(User, route_user)
        username = user.username
    client.post('/login', data={'username': username, 'password': 'routepass'})
    return client


class TestImportIndexRoute:
    def test_upload_page_requires_login(self, client, route_project):
        response = client.get(f'/projects/{route_project}/import')
        assert response.status_code == 302

    def test_upload_page_loads_for_owner(self, logged_client, route_project):
        response = logged_client.get(f'/projects/{route_project}/import')
        assert response.status_code == 200
        assert b'Importar Planejamento' in response.data

    def test_upload_page_shows_type_options(self, logged_client, route_project):
        response = logged_client.get(f'/projects/{route_project}/import')
        assert b'ms_project' in response.data
        assert b'primavera' in response.data

    def test_upload_page_has_autodetect_script(self, logged_client, route_project):
        response = logged_client.get(f'/projects/{route_project}/import')
        assert b'detected_type' in response.data

    def test_upload_no_file_flashes_error(self, logged_client, route_project):
        response = logged_client.post(
            f'/projects/{route_project}/import',
            data={'import_type': 'ms_project'},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert b'Nenhum arquivo selecionado' in response.data

    def test_upload_invalid_extension_flashes_error(self, logged_client, route_project):
        response = logged_client.post(
            f'/projects/{route_project}/import',
            data={
                'import_type': 'ms_project',
                'file': (io.BytesIO(b'data'), 'plan.csv'),
            },
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert b'Tipo de arquivo n' in response.data  # "Tipo de arquivo não suportado"

    def test_upload_valid_file_redirects_to_preview(self, logged_client, route_project):
        response = logged_client.post(
            f'/projects/{route_project}/import',
            data={
                'import_type': 'ms_project',
                'file': (io.BytesIO(MINIMAL_MS_XML), 'plan.xml'),
            },
            content_type='multipart/form-data',
        )
        assert response.status_code == 302
        location = response.headers['Location']
        assert f'/projects/{route_project}/import/preview' in location


class TestImportPreviewRoute:
    def _upload(self, client, project_id, xml=MINIMAL_MS_XML):
        """Helper: upload a file and follow redirect to preview."""
        client.post(
            f'/projects/{project_id}/import',
            data={
                'import_type': 'ms_project',
                'file': (io.BytesIO(xml), 'plan.xml'),
            },
            content_type='multipart/form-data',
        )

    def test_preview_without_upload_redirects(self, logged_client, route_project):
        """Preview page without session data redirects back to upload."""
        # Clear session by logging out and back in
        logged_client.get('/logout')
        logged_client.post('/login', data={'username': 'routeuser', 'password': 'routepass'})
        response = logged_client.get(
            f'/projects/{route_project}/import/preview', follow_redirects=True
        )
        assert b'Nenhum arquivo em preview' in response.data

    def test_preview_page_shows_task_table(self, logged_client, route_project):
        self._upload(logged_client, route_project)
        response = logged_client.get(f'/projects/{route_project}/import/preview')
        assert response.status_code == 200
        assert b'Task Alpha' in response.data

    def test_preview_shows_lock_baseline_checkbox(self, logged_client, route_project):
        self._upload(logged_client, route_project)
        response = logged_client.get(f'/projects/{route_project}/import/preview')
        assert b'lock_baseline' in response.data
        assert b'Travar baseline' in response.data

    def test_preview_cancel_redirects_to_upload(self, logged_client, route_project):
        self._upload(logged_client, route_project)
        response = logged_client.post(
            f'/projects/{route_project}/import/preview',
            data={'action': 'cancel'},
            follow_redirects=True,
        )
        assert b'Importa' in response.data  # "Importação cancelada" or upload page

    def test_preview_confirm_creates_log(self, logged_client, app, db, route_project):
        self._upload(logged_client, route_project)
        logged_client.post(
            f'/projects/{route_project}/import/preview',
            data={'action': 'confirm'},
        )
        with app.app_context():
            logs = ImportLog.query.filter_by(project_id=route_project).all()
            assert any(l.status == 'success' for l in logs)

    def test_preview_confirm_with_lock_baseline(self, logged_client, app, db, route_project):
        """Confirming with lock_baseline=1 should create a locked (closed) budget."""
        self._upload(logged_client, route_project)
        logged_client.post(
            f'/projects/{route_project}/import/preview',
            data={'action': 'confirm', 'lock_baseline': '1'},
        )
        with app.app_context():
            budget = (
                FinancialBudget.query
                .filter_by(project_id=route_project, status='closed')
                .order_by(FinancialBudget.id.desc())
                .first()
            )
            assert budget is not None
            assert budget.is_locked is True

    def test_preview_confirm_without_lock_baseline(self, logged_client, app, db, route_project):
        """Confirming without lock_baseline should create an active (unlocked) budget."""
        self._upload(logged_client, route_project)
        logged_client.post(
            f'/projects/{route_project}/import/preview',
            data={'action': 'confirm'},
        )
        with app.app_context():
            budget = (
                FinancialBudget.query
                .filter_by(project_id=route_project, status='active')
                .order_by(FinancialBudget.id.desc())
                .first()
            )
            assert budget is not None
            assert budget.is_locked is False


class TestImportLogRoute:
    def test_log_page_loads(self, logged_client, route_project):
        response = logged_client.get(f'/projects/{route_project}/import/log')
        assert response.status_code == 200
        assert b'Hist' in response.data  # "Histórico de Importações"

    def test_log_shows_imported_entries(self, logged_client, app, db, route_project, route_user):
        """After a successful import, the log page should list the entry."""
        with app.app_context():
            log = ImportLog(
                project_id=route_project,
                created_by=route_user,
                import_type='ms_project',
                file_name='visible.xml',
                status='success',
                total_tasks_imported=1,
                total_items_imported=0,
            )
            db.session.add(log)
            db.session.commit()

        response = logged_client.get(f'/projects/{route_project}/import/log')
        assert b'visible.xml' in response.data

    def test_rollback_success(self, logged_client, app, db, route_project, route_user):
        with app.app_context():
            log = ImportLog(
                project_id=route_project,
                created_by=route_user,
                import_type='ms_project',
                file_name='rollback_route.xml',
                status='success',
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

        response = logged_client.post(
            f'/projects/{route_project}/import/log/{log_id}/rollback',
            follow_redirects=True,
        )
        assert response.status_code == 200
        with app.app_context():
            refreshed = db.session.get(ImportLog, log_id)
            assert refreshed.status == 'failed'
