"""User model."""
from datetime import datetime, date
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and profile management."""

    __tablename__ = 'users'

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    full_name: str = db.Column(db.String(128))
    role: str = db.Column(db.String(32), default='engineer')
    is_active: bool = db.Column(db.Boolean, default=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Extended profile fields
<<<<<<< HEAD
    phone: Optional[str] = db.Column(db.String(20))
    job_title: Optional[str] = db.Column(db.String(128))
    company: Optional[str] = db.Column(db.String(128))
    supervisor: Optional[str] = db.Column(db.String(128))
    birth_date: Optional[date] = db.Column(db.Date)
    appointment_start_date: Optional[date] = db.Column(db.Date)
    measurement_criterion: Optional[str] = db.Column(db.String(64))
=======
    key: str = db.Column(db.String(64), unique=True, nullable=True, index=True)
    phone: str = db.Column(db.String(20), nullable=True)
    supervision: str = db.Column(db.String(64), nullable=True)
    function: str = db.Column(db.String(128), nullable=True)
    company: str = db.Column(db.String(64), nullable=True)
    state: str = db.Column(db.String(2), nullable=True)
    measurement_criteria: str = db.Column(db.String(64), nullable=True)
    birth_date: date = db.Column(db.Date, nullable=True)
    start_appointment_date: date = db.Column(db.Date, nullable=True)
    status: str = db.Column(db.String(32), default='Ativo', nullable=False)
    permissions: dict = db.Column(db.JSON, nullable=True)

    # Authentication & onboarding
    first_login: bool = db.Column(db.Boolean, default=True, nullable=False)
    password_reset_required: bool = db.Column(db.Boolean, default=False, nullable=False)
    last_login: datetime = db.Column(db.DateTime, nullable=True)
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1

    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Hash and set the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
