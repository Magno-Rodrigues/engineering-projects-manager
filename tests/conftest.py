"""Test configuration and fixtures."""
import pytest
from app import create_app, db as _db
from app.models.user import User
from app.models.project import Project


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from config import TestingConfig, config

    class SQLiteTestingConfig(TestingConfig):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        WTF_CSRF_ENABLED = False

    config['sqlite_testing'] = SQLiteTestingConfig
    app = create_app('sqlite_testing')
    return app


@pytest.fixture(scope='session')
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Create test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def test_user(db, app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()
