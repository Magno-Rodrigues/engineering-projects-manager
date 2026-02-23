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

    def test_anonymous_redirected_from_admin(self, client):
        """Anonymous users are redirected away from /admin."""
        response = client.get('/admin/')
        assert response.status_code == 302

    def test_non_admin_forbidden_from_admin(self, client, app, db):
        """Non-admin users receive 403 on /admin."""
        user = _create_user(db, app, 'eng_access', 'eng_access@example.com', role='engineer')
        client.post('/login', data={'username': 'eng_access', 'password': 'pass123'})
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_can_access_dashboard(self, client, app, db):
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

    @pytest.fixture(autouse=True)
    def reset_login_state(self):
        """Clear Flask-Login g state before each test to prevent cross-test pollution."""
        if hasattr(g, '_login_user'):
            del g._login_user
        yield
        if hasattr(g, '_login_user'):
            del g._login_user

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
