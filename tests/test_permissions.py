"""Tests for the module-based permission system."""
import pytest
from flask import g
from app import db
from app.models.user import User
from app.models.module_permission import ModulePermission
from app.models.user_module_permission import UserModulePermission
from app.services.permission_service import PermissionService


def _create_admin(db, username='perm_admin', email='perm_admin@example.com'):
    admin = User(username=username, email=email, role='admin')
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return admin


def _create_user(db, username='perm_user', email='perm_user@example.com'):
    user = User(username=username, email=email, role='engineer')
    user.set_password('userpass')
    db.session.add(user)
    db.session.commit()
    return user


def _create_module(db, module_name='projects', display_name='Projetos'):
    module = ModulePermission(module_name=module_name, display_name=display_name)
    db.session.add(module)
    db.session.commit()
    return module


class TestPermissionService:
    """Tests for PermissionService logic."""

    def test_has_module_access_no_permission(self, app, db):
        """User without permission has no module access."""
        with app.app_context():
            user = _create_user(db, 'ps_user1', 'ps_user1@example.com')
            assert PermissionService.has_module_access(user.id, 'projects') is False

    def test_has_module_access_with_read_permission(self, app, db):
        """User with read permission has module access."""
        with app.app_context():
            user = _create_user(db, 'ps_user2', 'ps_user2@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True)
            assert PermissionService.has_module_access(user.id, 'projects') is True

    def test_can_perform_action_create(self, app, db):
        """User with create permission can perform create action."""
        with app.app_context():
            user = _create_user(db, 'ps_user3', 'ps_user3@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_create=True)
            assert PermissionService.can_perform_action(user.id, 'projects', 'create') is True
            assert PermissionService.can_perform_action(user.id, 'projects', 'delete') is False

    def test_grant_and_revoke_permission(self, app, db):
        """Grant then revoke a module permission."""
        with app.app_context():
            user = _create_user(db, 'ps_user4', 'ps_user4@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True)
            assert PermissionService.has_module_access(user.id, 'projects') is True
            PermissionService.revoke_module_permission(user.id, 'projects')
            assert PermissionService.has_module_access(user.id, 'projects') is False

    def test_revoke_nonexistent_permission_returns_false(self, app, db):
        """Revoking a nonexistent permission returns False."""
        with app.app_context():
            user = _create_user(db, 'ps_user5', 'ps_user5@example.com')
            result = PermissionService.revoke_module_permission(user.id, 'nonexistent')
            assert result is False

    def test_get_user_modules_returns_list(self, app, db):
        """get_user_modules returns list of permissions."""
        with app.app_context():
            user = _create_user(db, 'ps_user6', 'ps_user6@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True)
            modules = PermissionService.get_user_modules(user.id)
            assert len(modules) >= 1
            assert any(m.module_name == 'projects' for m in modules)

    def test_get_available_modules(self, app, db):
        """get_available_modules returns active modules."""
        with app.app_context():
            _create_module(db, 'tasks_mod', 'Tarefas')
            modules = PermissionService.get_available_modules()
            assert len(modules) >= 1

    def test_update_permission_flags(self, app, db):
        """Granting again overwrites previous flags."""
        with app.app_context():
            user = _create_user(db, 'ps_user7', 'ps_user7@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True, can_create=True)
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True, can_create=False)
            perm = PermissionService.get_user_permission(user.id, 'projects')
            assert perm.can_read is True
            assert perm.can_create is False


class TestAdminPermissionsRoutes:
    """Tests for admin permission management routes."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_anonymous_cannot_access_permissoes(self, client):
        """Anonymous users cannot access /admin/permissoes."""
        response = client.get('/admin/permissoes')
        assert response.status_code in (302, 403)

    def test_regular_user_cannot_access_permissoes(self, client, app, db):
        """Regular users get 403 on /admin/permissoes."""
        with app.app_context():
            _create_user(db, 'route_user1', 'route_user1@example.com')
        client.post('/login', data={'username': 'route_user1', 'password': 'userpass'})
        response = client.get('/admin/permissoes')
        assert response.status_code == 403

    def test_admin_can_access_permissoes_index(self, client, app, db):
        """Admin can access the module permissions listing."""
        with app.app_context():
            _create_admin(db, 'route_admin1', 'route_admin1@example.com')
        client.post('/login', data={'username': 'route_admin1', 'password': 'adminpass'})
        response = client.get('/admin/permissoes')
        assert response.status_code == 200

    def test_admin_can_access_user_permissoes_page(self, client, app, db):
        """Admin can access the per-user permission edit page."""
        with app.app_context():
            _create_admin(db, 'route_admin2', 'route_admin2@example.com')
            target = _create_user(db, 'route_target1', 'route_target1@example.com')
            target_id = target.id
        client.post('/login', data={'username': 'route_admin2', 'password': 'adminpass'})
        response = client.get(f'/admin/permissoes/usuario/{target_id}')
        assert response.status_code == 200

    def test_admin_can_grant_module_permission_via_post(self, client, app, db):
        """Admin can grant a module permission via POST."""
        with app.app_context():
            _create_admin(db, 'route_admin3', 'route_admin3@example.com')
            target = _create_user(db, 'route_target2', 'route_target2@example.com')
            mod = _create_module(db, 'projects_route', 'Projetos Route')
            target_id = target.id
            mod_name = mod.module_name
        client.post('/login', data={'username': 'route_admin3', 'password': 'adminpass'})
        response = client.post(
            f'/admin/permissoes/usuario/{target_id}',
            data={f'{mod_name}_read': 'on', f'{mod_name}_create': 'on'},
        )
        assert response.status_code == 302
        with app.app_context():
            perm = PermissionService.get_user_permission(target_id, mod_name)
            assert perm is not None
            assert perm.can_read is True
            assert perm.can_create is True
            assert perm.can_delete is False

    def test_admin_can_revoke_module_permission_via_post(self, client, app, db):
        """Posting without any checkboxes for a module revokes its permission."""
        with app.app_context():
            _create_admin(db, 'route_admin4', 'route_admin4@example.com')
            target = _create_user(db, 'route_target3', 'route_target3@example.com')
            mod = _create_module(db, 'projects_revoke', 'Projetos Revoke')
            target_id = target.id
            mod_name = mod.module_name
            PermissionService.grant_module_permission(target_id, mod_name, can_read=True)
        client.post('/login', data={'username': 'route_admin4', 'password': 'adminpass'})
        # Post without any checkbox for this module → should revoke
        response = client.post(f'/admin/permissoes/usuario/{target_id}', data={})
        assert response.status_code == 302
        with app.app_context():
            perm = PermissionService.get_user_permission(target_id, mod_name)
            assert perm is None


class TestDisabledButtonsUI:
    """Tests that action buttons are disabled/enabled based on user permissions."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_dashboard_shows_disabled_button_without_create_permission(self, client, app, db):
        """User without module access sees disabled module card on dashboard."""
        with app.app_context():
            _create_user(db, 'btn_user1', 'btn_user1@example.com')
        client.post('/login', data={'username': 'btn_user1', 'password': 'userpass'})
        response = client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode()
        # Disabled module cards should be present
        assert 'cursor-not-allowed' in html

    def test_dashboard_shows_enabled_button_for_admin(self, client, app, db):
        """Admin user sees enabled module links on dashboard."""
        with app.app_context():
            _create_admin(db, 'btn_admin1', 'btn_admin1@example.com')
        client.post('/login', data={'username': 'btn_admin1', 'password': 'adminpass'})
        response = client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode()
        assert '/projects/' in html
        assert 'cursor-not-allowed' not in html

    def test_dashboard_shows_enabled_button_with_create_permission(self, client, app, db):
        """User with projects.create permission sees enabled projects link on dashboard."""
        with app.app_context():
            user = _create_user(db, 'btn_user2', 'btn_user2@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_create=True, can_read=True)
        client.post('/login', data={'username': 'btn_user2', 'password': 'userpass'})
        response = client.get('/projects/')
        assert response.status_code == 200
        html = response.data.decode()
        assert '/projects/new' in html

    def test_projects_index_shows_disabled_button_without_create_permission(self, client, app, db):
        """User with only projects.read sees disabled Novo Projeto button on index."""
        with app.app_context():
            user = _create_user(db, 'btn_user3', 'btn_user3@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True)
        client.post('/login', data={'username': 'btn_user3', 'password': 'userpass'})
        response = client.get('/projects/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'cursor-not-allowed' in html

    def test_projects_index_shows_enabled_button_with_create_permission(self, client, app, db):
        """User with projects.create permission sees enabled button on projects index."""
        with app.app_context():
            user = _create_user(db, 'btn_user4', 'btn_user4@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True, can_create=True)
        client.post('/login', data={'username': 'btn_user4', 'password': 'userpass'})
        response = client.get('/projects/')
        assert response.status_code == 200
        html = response.data.decode()
        assert '/projects/new' in html
        assert 'cursor-not-allowed' not in html

    def test_backend_still_blocks_create_without_permission(self, client, app, db):
        """Backend still returns 403 if user without projects.create tries to access create URL."""
        with app.app_context():
            user = _create_user(db, 'btn_user5', 'btn_user5@example.com')
            PermissionService.grant_module_permission(user.id, 'projects', can_read=True)
        client.post('/login', data={'username': 'btn_user5', 'password': 'userpass'})
        response = client.get('/projects/new')
        assert response.status_code == 403
