"""Tests for the admin dashboard and user management."""
import pytest
from flask import g
from app import db
from app.models.user import User


def _create_admin(db, username='admin_test', email='admin_test@example.com'):
    """Helper to create an admin user."""
    admin = User(username=username, email=email, role='admin')
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return username


def _create_regular_user(db, username='regular_test', email='regular_test@example.com'):
    """Helper to create a regular user."""
    user = User(username=username, email=email, role='engineer')
    user.set_password('userpass')
    db.session.add(user)
    db.session.commit()
    return username


class TestAdminAccess:
    """Tests for admin route access control."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_anonymous_user_cannot_access_admin(self, client):
        """Anonymous users are redirected away from /admin."""
        response = client.get('/admin/')
        assert response.status_code in (302, 403)

    def test_regular_user_gets_403_on_admin(self, client, app, db):
        """Regular (non-admin) users receive 403 on /admin routes."""
        _create_regular_user(db, 'reg_access', 'reg_access@example.com')
        client.post('/login', data={'username': 'reg_access', 'password': 'userpass'})
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_can_access_dashboard(self, client, app, db):
        """Admin users can access the /admin/ dashboard."""
        _create_admin(db, 'adm_dash', 'adm_dash@example.com')
        client.post('/login', data={'username': 'adm_dash', 'password': 'adminpass'})
        response = client.get('/admin/')
        assert response.status_code == 200

    def test_admin_can_access_usuarios_list(self, client, app, db):
        """Admin users can access the users list."""
        _create_admin(db, 'adm_list', 'adm_list@example.com')
        client.post('/login', data={'username': 'adm_list', 'password': 'adminpass'})
        response = client.get('/admin/usuarios')
        assert response.status_code == 200

    def test_regular_user_cannot_access_usuarios_list(self, client, app, db):
        """Regular users cannot access /admin/usuarios."""
        _create_regular_user(db, 'reg_list', 'reg_list@example.com')
        client.post('/login', data={'username': 'reg_list', 'password': 'userpass'})
        response = client.get('/admin/usuarios')
        assert response.status_code == 403


class TestAdminUserCRUD:
    """Tests for admin CRUD operations on users."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_admin_can_view_new_user_form(self, client, app, db):
        """Admin can GET the new user form."""
        _create_admin(db, 'adm_form', 'adm_form@example.com')
        client.post('/login', data={'username': 'adm_form', 'password': 'adminpass'})
        response = client.get('/admin/usuarios/novo')
        assert response.status_code == 200

    def test_admin_can_create_new_user(self, client, app, db):
        """Admin can POST to create a new user."""
        _create_admin(db, 'adm_create', 'adm_create@example.com')
        client.post('/login', data={'username': 'adm_create', 'password': 'adminpass'})
        response = client.post('/admin/usuarios/novo', data={
            'username': 'newuser_admin',
            'email': 'newuser_admin@example.com',
            'password': 'pass123',
            'full_name': 'Novo Usuário',
            'role': 'engineer',
            'key': 'KEY001',
            'status': 'Ativo',
        })
        assert response.status_code == 302
        created = User.query.filter_by(username='newuser_admin').first()
        assert created is not None
        assert created.key == 'KEY001'

    def test_create_user_duplicate_email_shows_error(self, client, app, db):
        """Creating a user with a duplicate email shows an error, not a 500."""
        _create_admin(db, 'adm_dup', 'adm_dup@example.com')
        client.post('/login', data={'username': 'adm_dup', 'password': 'adminpass'})
        # Create the first user
        client.post('/admin/usuarios/novo', data={
            'username': 'dupuser1',
            'email': 'dup_email@example.com',
            'password': 'pass123',
            'full_name': 'Dup 1',
            'role': 'engineer',
            'key': 'KEYDUP1',
            'status': 'Ativo',
        })
        # Try to create a second user with the same email
        response = client.post('/admin/usuarios/novo', data={
            'username': 'dupuser2',
            'email': 'dup_email@example.com',
            'password': 'pass123',
            'full_name': 'Dup 2',
            'role': 'engineer',
            'key': 'KEYDUP2',
            'status': 'Ativo',
        })
        assert response.status_code == 200  # Re-renders form with error

    def test_admin_can_edit_user(self, client, app, db):
        """Admin can edit an existing user."""
        _create_admin(db, 'adm_edit', 'adm_edit@example.com')
        client.post('/login', data={'username': 'adm_edit', 'password': 'adminpass'})
        # Create target user
        client.post('/admin/usuarios/novo', data={
            'username': 'edit_target',
            'email': 'edit_target@example.com',
            'password': 'pass123',
            'full_name': 'Edit Target',
            'role': 'engineer',
            'key': 'EDITKEY',
            'status': 'Ativo',
        })
        target = User.query.filter_by(username='edit_target').first()
        assert target is not None
        user_id = target.id

        response = client.post(f'/admin/usuarios/{user_id}/editar', data={
            'username': 'edit_target',
            'email': 'edit_target@example.com',
            'full_name': 'Nome Atualizado',
            'role': 'engineer',
            'key': 'EDITKEY',
            'status': 'Férias',
            'company': 'Vale',
        })
        assert response.status_code == 302
        db.session.expire_all()
        updated = db.session.get(User, user_id)
        assert updated.full_name == 'Nome Atualizado'
        assert updated.status == 'Férias'
        assert updated.company == 'Vale'

    def test_admin_can_delete_user(self, client, app, db):
        """Admin can delete a user."""
        _create_admin(db, 'adm_del', 'adm_del@example.com')
        client.post('/login', data={'username': 'adm_del', 'password': 'adminpass'})
        # Create target user
        client.post('/admin/usuarios/novo', data={
            'username': 'del_target',
            'email': 'del_target@example.com',
            'password': 'pass123',
            'full_name': 'Del Target',
            'role': 'engineer',
            'key': 'DELKEY',
            'status': 'Ativo',
        })
        target = User.query.filter_by(username='del_target').first()
        assert target is not None
        user_id = target.id

        response = client.post(f'/admin/usuarios/{user_id}/deletar')
        assert response.status_code == 302
        db.session.expire_all()
        deleted = db.session.get(User, user_id)
        assert deleted is None

    def test_admin_can_update_permissions(self, client, app, db):
        """Admin can update a user's permissions."""
        _create_admin(db, 'adm_perm', 'adm_perm@example.com')
        client.post('/login', data={'username': 'adm_perm', 'password': 'adminpass'})
        # Create target user
        client.post('/admin/usuarios/novo', data={
            'username': 'perm_target',
            'email': 'perm_target@example.com',
            'password': 'pass123',
            'full_name': 'Perm Target',
            'role': 'engineer',
            'key': 'PERMKEY',
            'status': 'Ativo',
        })
        target = User.query.filter_by(username='perm_target').first()
        assert target is not None
        user_id = target.id

        response = client.post(f'/admin/usuarios/{user_id}/permissoes', data={
            'can_edit_projects': 'on',
            'can_view_reports': 'on',
        })
        assert response.status_code == 302
        db.session.expire_all()
        updated = db.session.get(User, user_id)
        assert updated.permissions is not None
        assert updated.permissions.get('can_edit_projects') is True
        assert updated.permissions.get('can_edit_tasks') is False


class TestAdminServiceValidation:
    """Tests for AdminService validation logic."""

    def test_create_user_missing_username(self, app, db):
        """AdminService.create_user returns error for missing username."""
        from app.services.admin_service import AdminService
        user, error = AdminService.create_user({
            'username': '',
            'email': 'test@x.com',
            'password': 'pass',
        })
        assert user is None
        assert error is not None

    def test_create_user_missing_password(self, app, db):
        """AdminService.create_user returns error for missing password."""
        from app.services.admin_service import AdminService
        user, error = AdminService.create_user({
            'username': 'someuser',
            'email': 'someuser@x.com',
            'password': '',
        })
        assert user is None
        assert error is not None

    def test_parse_date_valid_formats(self, app, db):
        """AdminService._parse_date handles both date formats."""
        from app.services.admin_service import AdminService
        from datetime import date
        assert AdminService._parse_date('25/12/2000') == date(2000, 12, 25)
        assert AdminService._parse_date('2000-12-25') == date(2000, 12, 25)
        assert AdminService._parse_date('') is None
        assert AdminService._parse_date(None) is None
        assert AdminService._parse_date('not-a-date') is None

    def test_constants_are_non_empty(self, app, db):
        """All constant lists have at least one item."""
        from app.constants import (
            SUPERVISION_TYPES, COMPANIES, STATES,
            MEASUREMENT_CRITERIA, USER_STATUS, USER_ROLES,
        )
        assert len(SUPERVISION_TYPES) > 0
        assert len(COMPANIES) > 0
        assert len(STATES) == 27  # 27 Brazilian states/DF
        assert len(MEASUREMENT_CRITERIA) > 0
        assert len(USER_STATUS) > 0
        assert len(USER_ROLES) > 0


