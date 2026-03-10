"""Tests for time entry and measurement cycle functionality."""
import pytest
from datetime import date
from app.models.time_entry import MeasurementCycle, TimeEntry
from app.models.user import User
from app.models.project import Project
from app.services.timeentry_service import TimeEntryService
from app import db as _db


@pytest.fixture(scope='function')
def admin_user(db, app):
    """Create an admin user for testing."""
    with app.app_context():
        user = User(username='admin_te', email='admin_te@example.com', role='admin')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def regular_user(db, app):
    """Create a regular user for testing."""
    with app.app_context():
        user = User(username='user_te', email='user_te@example.com', role='engineer')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def test_project(db, app, admin_user):
    """Create a test project."""
    with app.app_context():
        admin = db.session.get(User, admin_user.id)
        project = Project(name='Test Project TE', owner_id=admin.id)
        db.session.add(project)
        db.session.commit()
        yield project
        db.session.delete(project)
        db.session.commit()


@pytest.fixture(scope='function')
def active_cycle(db, app, admin_user):
    """Create an active measurement cycle."""
    with app.app_context():
        cycle = MeasurementCycle(
            start_day=1,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            is_active=True,
            created_by=admin_user.id,
        )
        db.session.add(cycle)
        db.session.commit()
        yield cycle
        db.session.delete(cycle)
        db.session.commit()


class TestMeasurementCycleService:
    """Tests for MeasurementCycle via TimeEntryService."""

    def test_create_cycle_success(self, app, db, admin_user):
        """Test creating a valid measurement cycle."""
        with app.app_context():
            cycle, error = TimeEntryService.create_cycle(
                start_day=1,
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                is_active=False,
                created_by=admin_user.id,
            )
            assert error is None
            assert cycle is not None
            assert cycle.start_day == 1
            db.session.delete(cycle)
            db.session.commit()

    def test_create_cycle_invalid_start_day(self, app, db, admin_user):
        """Test that start_day must be 1-28."""
        with app.app_context():
            cycle, error = TimeEntryService.create_cycle(
                start_day=30,
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                is_active=False,
                created_by=admin_user.id,
            )
            assert cycle is None
            assert error is not None

    def test_create_cycle_end_before_start(self, app, db, admin_user):
        """Test that end_date must be after start_date."""
        with app.app_context():
            cycle, error = TimeEntryService.create_cycle(
                start_day=1,
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
                is_active=False,
                created_by=admin_user.id,
            )
            assert cycle is None
            assert error is not None

    def test_create_active_cycle_deactivates_previous(self, app, db, admin_user, active_cycle):
        """Creating a new active cycle should deactivate the previous one."""
        with app.app_context():
            new_cycle, error = TimeEntryService.create_cycle(
                start_day=1,
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                is_active=True,
                created_by=admin_user.id,
            )
            assert error is None
            # Reload old cycle
            old = db.session.get(MeasurementCycle, active_cycle.id)
            assert old.is_active is False
            db.session.delete(new_cycle)
            db.session.commit()

    def test_get_active_cycle(self, app, db, active_cycle):
        """Test get_active_cycle returns the active one."""
        with app.app_context():
            cycle = TimeEntryService.get_active_cycle()
            assert cycle is not None
            assert cycle.id == active_cycle.id

    def test_get_nonexistent_cycle(self, app, db):
        """Test get_cycle with unknown ID returns None."""
        with app.app_context():
            assert TimeEntryService.get_cycle(99999) is None


class TestTimeEntryService:
    """Tests for TimeEntry via TimeEntryService."""

    def test_create_entry_success(self, app, db, admin_user, test_project, active_cycle):
        """Test creating a valid time entry."""
        with app.app_context():
            entry, error = TimeEntryService.create_time_entry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Coding',
                work_date=date(2026, 2, 15),
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert error is None
            assert entry is not None
            assert entry.hours_worked == '08:00:00'
            db.session.delete(entry)
            db.session.commit()

    def test_create_entry_no_active_cycle(self, app, db, admin_user, test_project):
        """Test that creating an entry without an active cycle fails."""
        with app.app_context():
            # Ensure no cycle is active
            MeasurementCycle.query.filter_by(is_active=True).update({'is_active': False})
            db.session.commit()
            entry, error = TimeEntryService.create_time_entry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Coding',
                work_date=date(2026, 2, 15),
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert entry is None
            assert error is not None

    def test_create_entry_invalid_hours_format(self, app, db, admin_user, test_project, active_cycle):
        """Test that invalid hours format is rejected."""
        with app.app_context():
            entry, error = TimeEntryService.create_time_entry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Coding',
                work_date=date(2026, 2, 15),
                hours_worked='8:00',
                hour_type='Normal',
            )
            assert entry is None
            assert error is not None

    def test_create_entry_date_outside_cycle(self, app, db, admin_user, test_project, active_cycle):
        """Test that work_date outside active cycle is rejected."""
        with app.app_context():
            entry, error = TimeEntryService.create_time_entry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Coding',
                work_date=date(2026, 3, 5),
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert entry is None
            assert error is not None

    def test_create_entry_missing_activity(self, app, db, admin_user, test_project, active_cycle):
        """Test that missing main_activity is rejected."""
        with app.app_context():
            entry, error = TimeEntryService.create_time_entry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='',
                work_date=date(2026, 2, 15),
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert entry is None
            assert error is not None

    def test_delete_entry_regular_user_active_cycle(self, app, db, regular_user, test_project, active_cycle):
        """Regular user can delete their own entry in the active cycle."""
        with app.app_context():
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Testing',
                work_date=date(2026, 2, 10),
                hours_worked='04:00:00',
                hour_type='Normal',
                measurement_cycle_id=active_cycle.id,
            )
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id

            success, error = TimeEntryService.delete_time_entry(
                entry_id=entry_id,
                is_admin=False,
                current_user_id=regular_user.id,
            )
            assert success is True
            assert error is None

    def test_delete_entry_wrong_user(self, app, db, regular_user, admin_user, test_project, active_cycle):
        """Regular user cannot delete another user's entry."""
        with app.app_context():
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Testing',
                work_date=date(2026, 2, 10),
                hours_worked='04:00:00',
                hour_type='Normal',
                measurement_cycle_id=active_cycle.id,
            )
            db.session.add(entry)
            db.session.commit()

            success, error = TimeEntryService.delete_time_entry(
                entry_id=entry.id,
                is_admin=False,
                current_user_id=regular_user.id,
            )
            assert success is False
            assert error is not None
            db.session.delete(entry)
            db.session.commit()

    def test_delete_nonexistent_entry(self, app, db):
        """Test deleting nonexistent entry returns error."""
        with app.app_context():
            success, error = TimeEntryService.delete_time_entry(
                entry_id=99999,
                is_admin=True,
                current_user_id=1,
            )
            assert success is False
            assert error is not None

    def test_is_valid_hours(self, app, db):
        """Test hours format validation."""
        assert TimeEntry.is_valid_hours('08:00:00') is True
        assert TimeEntry.is_valid_hours('00:30:00') is True
        assert TimeEntry.is_valid_hours('8:00') is False
        assert TimeEntry.is_valid_hours('abc') is False
        assert TimeEntry.is_valid_hours(None) is False

    def test_update_entry_regular_user_work_date_outside_cycle(self, app, db, regular_user, test_project, active_cycle):
        """Regular user cannot update an entry whose work_date is outside the active cycle."""
        with app.app_context():
            # Entry has a work_date before the active cycle (2026-02-01 to 2026-02-28)
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Old work',
                work_date=date(2026, 1, 15),
                hours_worked='04:00:00',
                hour_type='Normal',
                measurement_cycle_id=None,
            )
            db.session.add(entry)
            db.session.commit()

            updated, error = TimeEntryService.update_time_entry(
                entry_id=entry.id,
                data={'main_activity': 'Updated work'},
                is_admin=False,
                current_user_id=regular_user.id,
            )
            assert updated is None
            assert error is not None
            db.session.delete(entry)
            db.session.commit()

    def test_update_entry_admin_work_date_outside_cycle(self, app, db, admin_user, test_project, active_cycle):
        """Admin can update an entry whose work_date is outside the active cycle."""
        with app.app_context():
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=admin_user.id,
                main_activity='Old work',
                work_date=date(2026, 1, 15),
                hours_worked='04:00:00',
                hour_type='Normal',
                measurement_cycle_id=None,
            )
            db.session.add(entry)
            db.session.commit()

            updated, error = TimeEntryService.update_time_entry(
                entry_id=entry.id,
                data={'main_activity': 'Updated by admin'},
                is_admin=True,
                current_user_id=admin_user.id,
            )
            assert updated is not None
            assert error is None
            db.session.delete(entry)
            db.session.commit()

    def test_delete_entry_regular_user_work_date_outside_cycle(self, app, db, regular_user, test_project, active_cycle):
        """Regular user cannot delete an entry whose work_date is outside the active cycle."""
        with app.app_context():
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Old work',
                work_date=date(2026, 1, 15),
                hours_worked='04:00:00',
                hour_type='Normal',
                measurement_cycle_id=None,
            )
            db.session.add(entry)
            db.session.commit()

            success, error = TimeEntryService.delete_time_entry(
                entry_id=entry.id,
                is_admin=False,
                current_user_id=regular_user.id,
            )
            assert success is False
            assert error is not None
            db.session.delete(entry)
            db.session.commit()


class TestTimeEntryCreateRoute:
    """Tests for the /apontamentos/new route (project dropdown population)."""

    @pytest.fixture(scope='function')
    def route_user(self, app, db):
        """Create a regular user for route tests."""
        with app.app_context():
            user = User(username='route_user_te', email='route_te@example.com', role='engineer')
            user.set_password('password')
            _db.session.add(user)
            _db.session.commit()
            user_id = user.id
        yield user_id
        with app.app_context():
            u = _db.session.get(User, user_id)
            if u:
                _db.session.delete(u)
                _db.session.commit()

    @pytest.fixture(scope='function')
    def logged_in_client(self, app, db, route_user):
        """Return an authenticated test client for route_user."""
        with app.test_client() as c:
            c.post('/login', data={'username': 'route_user_te', 'password': 'password'})
            yield c

    def test_create_page_requires_auth(self, client):
        """GET /apontamentos/new redirects unauthenticated users."""
        response = client.get('/apontamentos/new')
        assert response.status_code == 302

    def test_create_page_returns_200(self, logged_in_client):
        """GET /apontamentos/new returns 200 for authenticated users."""
        response = logged_in_client.get('/apontamentos/new')
        assert response.status_code == 200

    def test_create_page_includes_user_project_in_dropdown(self, app, db, route_user, logged_in_client):
        """GET /apontamentos/new includes the user's project in the dropdown HTML."""
        with app.app_context():
            project = Project(name='My Route Project', owner_id=route_user)
            _db.session.add(project)
            _db.session.commit()
            project_id = project.id

        response = logged_in_client.get('/apontamentos/new')
        assert response.status_code == 200
        assert b'My Route Project' in response.data

        with app.app_context():
            p = _db.session.get(Project, project_id)
            if p:
                _db.session.delete(p)
                _db.session.commit()

    def test_create_page_dropdown_has_default_option(self, logged_in_client):
        """GET /apontamentos/new contains the default placeholder option."""
        response = logged_in_client.get('/apontamentos/new')
        assert b'Selecione um projeto' in response.data


class TestBulkAndPendingService:
    """Tests for bulk creation and pending dates helpers."""

    def test_generate_weekday_dates_skip_weekends(self, app, db):
        """generate_weekday_dates excludes Sat/Sun when skip_weekends=True."""
        with app.app_context():
            # 2026-03-09 (Mon) to 2026-03-15 (Sun)
            dates = TimeEntryService.generate_weekday_dates(
                date(2026, 3, 9), date(2026, 3, 15), skip_weekends=True
            )
            assert len(dates) == 5
            for d in dates:
                assert d.weekday() < 5

    def test_generate_weekday_dates_include_weekends(self, app, db):
        """generate_weekday_dates includes weekends when skip_weekends=False."""
        with app.app_context():
            dates = TimeEntryService.generate_weekday_dates(
                date(2026, 3, 9), date(2026, 3, 15), skip_weekends=False
            )
            assert len(dates) == 7

    def test_generate_weekday_dates_same_day(self, app, db):
        """generate_weekday_dates for start==end returns one weekday or zero."""
        with app.app_context():
            # 2026-03-09 is a Monday
            dates = TimeEntryService.generate_weekday_dates(
                date(2026, 3, 9), date(2026, 3, 9)
            )
            assert dates == [date(2026, 3, 9)]

    def test_get_pending_cycle_dates_all_pending(self, app, db, regular_user, active_cycle):
        """All weekdays are pending when no entries exist."""
        with app.app_context():
            all_weekdays, entered, pending, future, completed = \
                TimeEntryService.get_pending_cycle_dates(regular_user.id, active_cycle)
            assert len(completed) == 0
            assert len(all_weekdays) == len(pending) + len(future)

    def test_get_pending_cycle_dates_after_entry(self, app, db, regular_user, test_project, active_cycle):
        """A date with an entry is marked completed, not pending."""
        with app.app_context():
            entry = TimeEntry(
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Work',
                work_date=date(2026, 2, 2),
                hours_worked='08:00:00',
                hour_type='Normal',
                measurement_cycle_id=active_cycle.id,
            )
            _db.session.add(entry)
            _db.session.commit()

            _, entered, pending, future, completed = \
                TimeEntryService.get_pending_cycle_dates(regular_user.id, active_cycle)
            assert date(2026, 2, 2) in entered
            assert date(2026, 2, 2) in completed
            assert date(2026, 2, 2) not in pending

            _db.session.delete(entry)
            _db.session.commit()

    def test_create_bulk_time_entries_success(self, app, db, regular_user, test_project, active_cycle):
        """create_bulk_time_entries creates one entry per provided date."""
        with app.app_context():
            dates = [date(2026, 2, 2), date(2026, 2, 3)]
            entries, errors = TimeEntryService.create_bulk_time_entries(
                dates=dates,
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Bulk Test',
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert len(entries) == 2
            assert errors == []
            for e in entries:
                _db.session.delete(e)
            _db.session.commit()

    def test_create_bulk_time_entries_partial_errors(self, app, db, regular_user, test_project, active_cycle):
        """Dates outside the active cycle produce errors; valid ones succeed."""
        with app.app_context():
            dates = [
                date(2026, 2, 2),   # inside cycle
                date(2026, 1, 5),   # outside cycle
            ]
            entries, errors = TimeEntryService.create_bulk_time_entries(
                dates=dates,
                project_id=test_project.id,
                user_id=regular_user.id,
                main_activity='Bulk Test',
                hours_worked='08:00:00',
                hour_type='Normal',
            )
            assert len(entries) == 1
            assert len(errors) == 1
            for e in entries:
                _db.session.delete(e)
            _db.session.commit()
