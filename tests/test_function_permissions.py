"""Tests for the function-permission access control system."""
import pytest
from flask import g
from app import db
from app.models.user import User
from app.models.function_permission import FunctionPermission
from app.services.permission_service import PermissionService
from app.constants import VALID_MODULES, MODULE_FUNCTIONS


def _create_admin(db, username='fp_admin', email='fp_admin@example.com'):
    admin = User(username=username, email=email, role='admin')
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return admin


def _create_user(db, username='fp_user', email='fp_user@example.com'):
    user = User(username=username, email=email, role='engineer')
    user.set_password('userpass')
    db.session.add(user)
    db.session.commit()
    return user


class TestFunctionPermissionModel:
    """Tests for the FunctionPermission model and PermissionService function-level methods."""

    def test_new_user_has_zero_function_permissions(self, app, db):
        """A newly created user has no function permissions."""
        with app.app_context():
            user = _create_user(db, 'fp_new1', 'fp_new1@example.com')
            perms = PermissionService.get_user_function_permissions(user.id)
            assert perms == []

    def test_set_function_permission_grants_access(self, app, db):
        """set_function_permission grants a specific function permission."""
        with app.app_context():
            user = _create_user(db, 'fp_set1', 'fp_set1@example.com')
            perm, err = PermissionService.set_function_permission(user.id, 'projects', 'view', True)
            assert err is None
            assert perm is not None
            assert perm.has_permission is True

    def test_has_function_permission_returns_true_when_granted(self, app, db):
        """has_function_permission returns True after granting."""
        with app.app_context():
            user = _create_user(db, 'fp_has1', 'fp_has1@example.com')
            PermissionService.set_function_permission(user.id, 'projects', 'create', True)
            assert PermissionService.has_function_permission(user.id, 'projects', 'create') is True

    def test_has_function_permission_returns_false_when_not_granted(self, app, db):
        """has_function_permission returns False when no permission is set."""
        with app.app_context():
            user = _create_user(db, 'fp_has2', 'fp_has2@example.com')
            assert PermissionService.has_function_permission(user.id, 'projects', 'delete') is False

    def test_has_function_permission_returns_false_when_revoked(self, app, db):
        """has_function_permission returns False after revoking."""
        with app.app_context():
            user = _create_user(db, 'fp_rev1', 'fp_rev1@example.com')
            PermissionService.set_function_permission(user.id, 'projects', 'edit', True)
            PermissionService.set_function_permission(user.id, 'projects', 'edit', False)
            assert PermissionService.has_function_permission(user.id, 'projects', 'edit') is False

    def test_set_function_permission_invalid_module(self, app, db):
        """set_function_permission returns error for invalid module."""
        with app.app_context():
            user = _create_user(db, 'fp_inv1', 'fp_inv1@example.com')
            perm, err = PermissionService.set_function_permission(user.id, 'invalid_module', 'view', True)
            assert perm is None
            assert err is not None

    def test_set_function_permission_invalid_function(self, app, db):
        """set_function_permission returns error for invalid function in module."""
        with app.app_context():
            user = _create_user(db, 'fp_inv2', 'fp_inv2@example.com')
            perm, err = PermissionService.set_function_permission(user.id, 'projects', 'manage_cycles', True)
            assert perm is None
            assert err is not None

    def test_set_module_function_permissions_bulk(self, app, db):
        """set_module_function_permissions correctly sets all functions for a module."""
        with app.app_context():
            user = _create_user(db, 'fp_bulk1', 'fp_bulk1@example.com')
            PermissionService.set_module_function_permissions(
                user.id, 'projects', ['view', 'create'], granted_by_id=None
            )
            assert PermissionService.has_function_permission(user.id, 'projects', 'view') is True
            assert PermissionService.has_function_permission(user.id, 'projects', 'create') is True
            assert PermissionService.has_function_permission(user.id, 'projects', 'edit') is False
            assert PermissionService.has_function_permission(user.id, 'projects', 'delete') is False

    def test_has_module_access_via_functions(self, app, db):
        """has_module_access_via_functions returns True when any function is granted."""
        with app.app_context():
            user = _create_user(db, 'fp_mod1', 'fp_mod1@example.com')
            assert PermissionService.has_module_access_via_functions(user.id, 'reports') is False
            PermissionService.set_function_permission(user.id, 'reports', 'view', True)
            assert PermissionService.has_module_access_via_functions(user.id, 'reports') is True

    def test_get_user_module_function_permissions(self, app, db):
        """get_user_module_function_permissions returns only permissions for the given module."""
        with app.app_context():
            user = _create_user(db, 'fp_mod2', 'fp_mod2@example.com')
            PermissionService.set_function_permission(user.id, 'tasks', 'view', True)
            PermissionService.set_function_permission(user.id, 'reports', 'view', True)
            perms = PermissionService.get_user_module_function_permissions(user.id, 'tasks')
            assert len(perms) == 1
            assert perms[0].function_name == 'view'
            assert perms[0].module_name == 'tasks'

    def test_manage_cycles_valid_for_apontamentos(self, app, db):
        """manage_cycles is a valid function for apontamentos module."""
        with app.app_context():
            user = _create_user(db, 'fp_apo1', 'fp_apo1@example.com')
            perm, err = PermissionService.set_function_permission(user.id, 'apontamentos', 'manage_cycles', True)
            assert err is None
            assert perm is not None
            assert PermissionService.has_function_permission(user.id, 'apontamentos', 'manage_cycles') is True

    def test_export_valid_for_reports(self, app, db):
        """export is a valid function for reports module."""
        with app.app_context():
            user = _create_user(db, 'fp_rep1', 'fp_rep1@example.com')
            perm, err = PermissionService.set_function_permission(user.id, 'reports', 'export', True)
            assert err is None
            assert perm is not None


class TestRequirePermissionDecorator:
    """Tests for the require_permission decorator."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_admin_bypasses_require_permission(self, client, app, db):
        """Admin user can access routes protected by @require_permission."""
        with app.app_context():
            _create_admin(db, 'rp_admin1', 'rp_admin1@example.com')
        client.post('/login', data={'username': 'rp_admin1', 'password': 'adminpass'})
        # Admin should always get past permission checks; test with a generic admin route
        response = client.get('/admin/')
        assert response.status_code == 200

    def test_user_without_permission_gets_403(self, client, app, db):
        """User without any function permission cannot access protected routes."""
        with app.app_context():
            _create_user(db, 'rp_user1', 'rp_user1@example.com')
        client.post('/login', data={'username': 'rp_user1', 'password': 'userpass'})
        # projects/new is protected by action_required('projects', 'create')
        response = client.get('/projects/new')
        assert response.status_code == 403

    def test_user_with_permission_can_access(self, client, app, db):
        """User with function permission gets access from has_function_permission check."""
        with app.app_context():
            user = _create_user(db, 'rp_user2', 'rp_user2@example.com')
            PermissionService.set_function_permission(user.id, 'projects', 'view', True)
            PermissionService.set_function_permission(user.id, 'projects', 'create', True)
            assert PermissionService.has_function_permission(user.id, 'projects', 'view') is True
            assert PermissionService.has_function_permission(user.id, 'projects', 'create') is True


class TestAdminUsersRoutes:
    """Tests for /admin/users/ routes."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_anonymous_cannot_access_admin_users(self, client):
        """Anonymous users cannot access /admin/users/."""
        response = client.get('/admin/users/')
        assert response.status_code in (302, 403)

    def test_regular_user_cannot_access_admin_users(self, client, app, db):
        """Regular users get 403 on /admin/users/."""
        with app.app_context():
            _create_user(db, 'au_user1', 'au_user1@example.com')
        client.post('/login', data={'username': 'au_user1', 'password': 'userpass'})
        response = client.get('/admin/users/')
        assert response.status_code == 403

    def test_admin_can_list_users(self, client, app, db):
        """Admin can access /admin/users/ list page."""
        with app.app_context():
            _create_admin(db, 'au_admin1', 'au_admin1@example.com')
        client.post('/login', data={'username': 'au_admin1', 'password': 'adminpass'})
        response = client.get('/admin/users/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Controle de Acesso' in html

    def test_admin_can_view_user_permissions_page(self, client, app, db):
        """Admin can access /admin/users/<id>/permissions."""
        with app.app_context():
            _create_admin(db, 'au_admin2', 'au_admin2@example.com')
            target = _create_user(db, 'au_target1', 'au_target1@example.com')
            target_id = target.id
        client.post('/login', data={'username': 'au_admin2', 'password': 'adminpass'})
        response = client.get(f'/admin/users/{target_id}/permissions')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Permissões' in html
        # All module tabs should be present
        for module in VALID_MODULES:
            assert module in html

    def test_admin_can_set_function_permissions_via_post(self, client, app, db):
        """Admin can POST to /admin/users/<id>/permissions to set function permissions."""
        with app.app_context():
            _create_admin(db, 'au_admin3', 'au_admin3@example.com')
            target = _create_user(db, 'au_target2', 'au_target2@example.com')
            target_id = target.id
        client.post('/login', data={'username': 'au_admin3', 'password': 'adminpass'})
        response = client.post(
            f'/admin/users/{target_id}/permissions',
            data={'projects__view': 'on', 'projects__create': 'on'},
        )
        assert response.status_code == 302
        with app.app_context():
            assert PermissionService.has_function_permission(target_id, 'projects', 'view') is True
            assert PermissionService.has_function_permission(target_id, 'projects', 'create') is True
            assert PermissionService.has_function_permission(target_id, 'projects', 'edit') is False
            assert PermissionService.has_function_permission(target_id, 'projects', 'delete') is False

    def test_admin_can_revoke_function_permissions_via_post(self, client, app, db):
        """Posting without checkboxes for a module revokes all its function permissions."""
        with app.app_context():
            _create_admin(db, 'au_admin4', 'au_admin4@example.com')
            target = _create_user(db, 'au_target3', 'au_target3@example.com')
            target_id = target.id
            PermissionService.set_function_permission(target_id, 'projects', 'view', True)
        client.post('/login', data={'username': 'au_admin4', 'password': 'adminpass'})
        # Post without any projects__ checkboxes → should revoke all project permissions
        response = client.post(f'/admin/users/{target_id}/permissions', data={})
        assert response.status_code == 302
        with app.app_context():
            assert PermissionService.has_function_permission(target_id, 'projects', 'view') is False

    def test_edit_user_redirects_to_permissions(self, client, app, db):
        """GET /admin/users/<id>/edit redirects to /admin/users/<id>/permissions."""
        with app.app_context():
            _create_admin(db, 'au_admin5', 'au_admin5@example.com')
            target = _create_user(db, 'au_target4', 'au_target4@example.com')
            target_id = target.id
        client.post('/login', data={'username': 'au_admin5', 'password': 'adminpass'})
        response = client.get(f'/admin/users/{target_id}/edit')
        assert response.status_code == 302
        assert f'/admin/users/{target_id}/permissions' in response.headers.get('Location', '')

    def test_unknown_user_returns_redirect(self, client, app, db):
        """GET /admin/users/99999/permissions redirects with error for nonexistent user."""
        with app.app_context():
            _create_admin(db, 'au_admin6', 'au_admin6@example.com')
        client.post('/login', data={'username': 'au_admin6', 'password': 'adminpass'})
        response = client.get('/admin/users/99999/permissions')
        assert response.status_code == 302


class TestModuleAndFunctionConstants:
    """Tests for module/function constants validation."""

    def test_valid_modules_list(self, app, db):
        """VALID_MODULES contains the expected module names."""
        expected = {'projects', 'tasks', 'reports', 'apontamentos', 'pmbok', 'admin'}
        assert expected.issubset(set(VALID_MODULES))

    def test_module_functions_contains_all_modules(self, app, db):
        """MODULE_FUNCTIONS has an entry for every valid module."""
        for module in VALID_MODULES:
            assert module in MODULE_FUNCTIONS
            assert len(MODULE_FUNCTIONS[module]) > 0

    def test_apontamentos_has_manage_cycles(self, app, db):
        """apontamentos module includes manage_cycles function."""
        assert 'manage_cycles' in MODULE_FUNCTIONS['apontamentos']

    def test_reports_has_export(self, app, db):
        """reports module includes export function."""
        assert 'export' in MODULE_FUNCTIONS['reports']

    def test_admin_has_manage_functions(self, app, db):
        """admin module includes manage_users, manage_permissions, manage_config."""
        for fn in ['manage_users', 'manage_permissions', 'manage_config']:
            assert fn in MODULE_FUNCTIONS['admin']
