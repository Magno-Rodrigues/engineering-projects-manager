<<<<<<< HEAD
"""Tests for admin panel functionality."""
import pytest
from flask import g
from app.models.user import User


def _create_user(db, app, username, email, role='engineer', password='pass123'):
    """Helper to create and persist a user, returning it attached to the session."""
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user
=======
"""Tests for the admin dashboard and user management."""
import pytest
from unittest.mock import patch, MagicMock
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
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1


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

<<<<<<< HEAD
    def test_anonymous_redirected_from_admin(self, client):
        """Anonymous users are redirected away from /admin."""
        response = client.get('/admin/')
        assert response.status_code == 302

    def test_non_admin_forbidden_from_admin(self, client, app, db):
        """Non-admin users receive 403 on /admin."""
        user = _create_user(db, app, 'eng_access', 'eng_access@example.com', role='engineer')
        client.post('/login', data={'username': 'eng_access', 'password': 'pass123'})
=======
    def test_anonymous_user_cannot_access_admin(self, client):
        """Anonymous users are redirected away from /admin."""
        response = client.get('/admin/')
        assert response.status_code in (302, 403)

    def test_regular_user_gets_403_on_admin(self, client, app, db):
        """Regular (non-admin) users receive 403 on /admin routes."""
        _create_regular_user(db, 'reg_access', 'reg_access@example.com')
        client.post('/login', data={'username': 'reg_access', 'password': 'userpass'})
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_can_access_dashboard(self, client, app, db):
<<<<<<< HEAD
        """Admin users can access /admin."""
        _create_user(db, app, 'admin_dash', 'admin_dash@example.com', role='admin')
        client.post('/login', data={'username': 'admin_dash', 'password': 'pass123'})
        response = client.get('/admin/')
        assert response.status_code == 200

    def test_non_admin_forbidden_from_users_list(self, client, app, db):
        """Non-admin users receive 403 on /admin/users."""
        _create_user(db, app, 'eng_list', 'eng_list@example.com', role='engineer')
        client.post('/login', data={'username': 'eng_list', 'password': 'pass123'})
        response = client.get('/admin/users')
        assert response.status_code == 403

    def test_admin_can_access_users_list(self, client, app, db):
        """Admin can access /admin/users."""
        _create_user(db, app, 'admin_list', 'admin_list@example.com', role='admin')
        client.post('/login', data={'username': 'admin_list', 'password': 'pass123'})
        response = client.get('/admin/users')
        assert response.status_code == 200


class TestAdminUserCRUD:
    """Tests for admin user CRUD routes."""
=======
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
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

<<<<<<< HEAD
    def _login_as_admin(self, client, app, db, username, email):
        _create_user(db, app, username, email, role='admin')
        client.post('/login', data={'username': username, 'password': 'pass123'})

    def test_create_user_form_loads(self, client, app, db):
        """Admin can load the create user form."""
        self._login_as_admin(client, app, db, 'admin_form', 'admin_form@example.com')
        response = client.get('/admin/users/new')
        assert response.status_code == 200

    def test_create_user_success(self, client, app, db):
        """Admin can create a new user via POST."""
        self._login_as_admin(client, app, db, 'admin_create', 'admin_create@example.com')
        response = client.post('/admin/users/new', data={
            'username': 'newuser_admin',
            'email': 'newuser_admin@example.com',
            'password': 'securepass',
            'full_name': 'New User',
            'role': 'engineer',
            'status': 'active',
        })
        assert response.status_code == 302
        with app.app_context():
            created = User.query.filter_by(username='newuser_admin').first()
            assert created is not None
            assert created.role == 'engineer'

    def test_create_user_duplicate_username(self, client, app, db):
        """Creating a user with a duplicate username shows an error."""
        self._login_as_admin(client, app, db, 'admin_dup', 'admin_dup@example.com')
        # Create target user first
        _create_user(db, app, 'dup_target', 'dup_target@example.com', role='engineer')
        response = client.post('/admin/users/new', data={
            'username': 'dup_target',
            'email': 'other_dup@example.com',
            'password': 'pass',
            'role': 'engineer',
            'status': 'active',
        })
        assert response.status_code == 200  # stays on form with error

    def test_edit_user_form_loads(self, client, app, db):
        """Admin can load the edit user form."""
        self._login_as_admin(client, app, db, 'admin_edit_load', 'admin_edit_load@example.com')
        target = _create_user(db, app, 'edit_target', 'edit_target@example.com')
        response = client.get(f'/admin/users/{target.id}/edit')
        assert response.status_code == 200

    def test_edit_user_success(self, client, app, db):
        """Admin can update a user via POST."""
        self._login_as_admin(client, app, db, 'admin_edit', 'admin_edit@example.com')
        target = _create_user(db, app, 'edit_user', 'edit_user@example.com')
        response = client.post(f'/admin/users/{target.id}/edit', data={
            'username': 'edit_user',
            'email': 'edit_user@example.com',
            'password': '',
            'full_name': 'Updated Name',
            'role': 'manager',
            'status': 'active',
        })
        assert response.status_code == 302
        with app.app_context():
            updated = db.session.get(User, target.id)
            assert updated.full_name == 'Updated Name'
            assert updated.role == 'manager'

    def test_edit_nonexistent_user_redirects(self, client, app, db):
        """Editing a non-existent user redirects to list with error."""
        self._login_as_admin(client, app, db, 'admin_edit_nx', 'admin_edit_nx@example.com')
        response = client.get('/admin/users/99999/edit')
        assert response.status_code == 302

    def test_delete_user_success(self, client, app, db):
        """Admin can delete a user."""
        self._login_as_admin(client, app, db, 'admin_del', 'admin_del@example.com')
        target = _create_user(db, app, 'del_target', 'del_target@example.com')
        response = client.post(f'/admin/users/{target.id}/delete')
        assert response.status_code == 302
        with app.app_context():
            assert db.session.get(User, target.id) is None

    def test_bulk_delete_users(self, client, app, db):
        """Admin can bulk-delete multiple users."""
        self._login_as_admin(client, app, db, 'admin_bulk', 'admin_bulk@example.com')
        u1 = _create_user(db, app, 'bulk1', 'bulk1@example.com')
        u2 = _create_user(db, app, 'bulk2', 'bulk2@example.com')
        response = client.post('/admin/users/bulk-delete', data={
            'user_ids': [str(u1.id), str(u2.id)],
        })
        assert response.status_code == 302
        with app.app_context():
            assert db.session.get(User, u1.id) is None
            assert db.session.get(User, u2.id) is None

    def test_bulk_delete_no_ids_redirects(self, client, app, db):
        """Bulk delete with no IDs redirects with a warning."""
        self._login_as_admin(client, app, db, 'admin_bulk_empty', 'admin_bulk_empty@example.com')
        response = client.post('/admin/users/bulk-delete', data={})
        assert response.status_code == 302


class TestAdminService:
    """Tests for AdminService methods."""

    def test_list_all_users(self, app, db):
        """list_all_users returns all users."""
        from app.services.admin_service import AdminService
        with app.app_context():
            users = AdminService.list_all_users()
            assert isinstance(users, list)

    def test_list_users_with_search_key(self, app, db):
        """list_all_users filters by username."""
        from app.services.admin_service import AdminService
        user = User(username='searchable_key', email='searchable_key@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        with app.app_context():
            results = AdminService.list_all_users(search_key='searchable_key')
            assert any(u.username == 'searchable_key' for u in results)
        db.session.delete(user)
        db.session.commit()

    def test_get_user_by_id(self, app, db):
        """get_user_by_id returns the correct user."""
        from app.services.admin_service import AdminService
        user = User(username='getbyid', email='getbyid@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        with app.app_context():
            fetched = AdminService.get_user_by_id(user.id)
            assert fetched is not None
            assert fetched.username == 'getbyid'
        db.session.delete(user)
        db.session.commit()

    def test_get_user_by_id_not_found(self, app, db):
        """get_user_by_id returns None for unknown ID."""
        from app.services.admin_service import AdminService
        with app.app_context():
            assert AdminService.get_user_by_id(99999) is None

    def test_create_user(self, app, db):
        """create_user creates a new user."""
        from app.services.admin_service import AdminService
        with app.app_context():
            user, error = AdminService.create_user({
                'username': 'svc_create',
                'email': 'svc_create@example.com',
                'password': 'pass123',
                'role': 'engineer',
            })
            assert error is None
            assert user is not None
            assert user.username == 'svc_create'

    def test_update_user(self, app, db):
        """update_user modifies existing user fields."""
        from app.services.admin_service import AdminService
        user = User(username='svc_update', email='svc_update@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        with app.app_context():
            updated, error = AdminService.update_user(user.id, {'full_name': 'Updated'})
            assert error is None
            assert updated.full_name == 'Updated'

    def test_delete_user(self, app, db):
        """delete_user removes the user."""
        from app.services.admin_service import AdminService
        user = User(username='svc_delete', email='svc_delete@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        with app.app_context():
            ok, err = AdminService.delete_user(uid)
            assert ok is True
            assert err is None

    def test_delete_multiple_users(self, app, db):
        """delete_multiple_users removes all given users."""
        from app.services.admin_service import AdminService
        u1 = User(username='svc_bulk1', email='svc_bulk1@example.com')
        u1.set_password('pass')
        u2 = User(username='svc_bulk2', email='svc_bulk2@example.com')
        u2.set_password('pass')
        db.session.add_all([u1, u2])
        db.session.commit()
        with app.app_context():
            deleted, not_found = AdminService.delete_multiple_users([u1.id, u2.id])
            assert deleted == 2
            assert not_found == []
=======
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


class TestAdminEmailRouting:
    """Tests that creation and editing routes send the correct emails."""

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

    def test_new_user_sends_registration_and_admin_emails(self, client, app, db):
        """Creating a new user sends welcome + admin notification, NOT password-reset."""
        _create_admin(db, 'adm_email1', 'adm_email1@example.com')
        client.post('/login', data={'username': 'adm_email1', 'password': 'adminpass'})

        with patch('app.services.email_service.send_user_registration_email', return_value=True) as mock_reg, \
             patch('app.services.email_service.send_admin_registration_notification', return_value=True) as mock_adm, \
             patch('app.services.email_service.send_password_reset_email', return_value=True) as mock_reset, \
             patch('app.services.email_service.generate_reset_token') as mock_token:
            mock_token.return_value = MagicMock(token='fake-token')
            client.post('/admin/usuarios/novo', data={
                'username': 'emailtest1',
                'email': 'emailtest1@example.com',
                'password': 'pass123',
                'full_name': 'Email Test',
                'role': 'engineer',
                'key': 'EKEY1',
                'status': 'Ativo',
            })

        mock_reg.assert_called_once()
        mock_adm.assert_called_once()
        mock_reset.assert_not_called()

    def test_edit_user_with_password_sends_only_reset_email(self, client, app, db):
        """Editing a user with a new password sends only the password-reset email."""
        _create_admin(db, 'adm_email2', 'adm_email2@example.com')
        client.post('/login', data={'username': 'adm_email2', 'password': 'adminpass'})

        # Create a target user first
        client.post('/admin/usuarios/novo', data={
            'username': 'edit_email_target',
            'email': 'edit_email_target@example.com',
            'password': 'pass123',
            'full_name': 'Edit Email Target',
            'role': 'engineer',
            'key': 'EKEY2',
            'status': 'Ativo',
        })
        target = User.query.filter_by(username='edit_email_target').first()

        with patch('app.services.email_service.send_password_reset_email', return_value=True) as mock_reset, \
             patch('app.services.email_service.send_user_registration_email', return_value=True) as mock_reg, \
             patch('app.services.email_service.send_admin_registration_notification', return_value=True) as mock_adm, \
             patch('app.services.email_service.generate_reset_token') as mock_token:
            mock_token.return_value = MagicMock(token='fake-token')
            client.post(f'/admin/usuarios/{target.id}/editar', data={
                'username': 'edit_email_target',
                'email': 'edit_email_target@example.com',
                'full_name': 'Edit Email Target',
                'role': 'engineer',
                'key': 'EKEY2',
                'status': 'Ativo',
                'password': 'newpass456',
            })

        mock_reset.assert_called_once()
        mock_reg.assert_not_called()
        mock_adm.assert_not_called()

    def test_edit_user_without_password_sends_no_email(self, client, app, db):
        """Editing a user without changing the password sends no email at all."""
        _create_admin(db, 'adm_email3', 'adm_email3@example.com')
        client.post('/login', data={'username': 'adm_email3', 'password': 'adminpass'})

        client.post('/admin/usuarios/novo', data={
            'username': 'nopwd_email_target',
            'email': 'nopwd_email_target@example.com',
            'password': 'pass123',
            'full_name': 'No Password Target',
            'role': 'engineer',
            'key': 'EKEY3',
            'status': 'Ativo',
        })
        target = User.query.filter_by(username='nopwd_email_target').first()

        with patch('app.services.email_service.send_password_reset_email', return_value=True) as mock_reset, \
             patch('app.services.email_service.send_user_registration_email', return_value=True) as mock_reg, \
             patch('app.services.email_service.send_admin_registration_notification', return_value=True) as mock_adm:
            client.post(f'/admin/usuarios/{target.id}/editar', data={
                'username': 'nopwd_email_target',
                'email': 'nopwd_email_target@example.com',
                'full_name': 'No Password Target Updated',
                'role': 'engineer',
                'key': 'EKEY3',
                'status': 'Ativo',
                'password': '',
            })

        mock_reset.assert_not_called()
        mock_reg.assert_not_called()
        mock_adm.assert_not_called()


>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
