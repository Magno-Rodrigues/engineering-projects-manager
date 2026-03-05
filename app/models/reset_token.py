"""Password reset token model."""
from datetime import datetime, timezone
from app import db


class PasswordResetToken(db.Model):
    """Token used for password reset flow."""

    __tablename__ = 'password_reset_tokens'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token: str = db.Column(db.String(255), unique=True, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: datetime = db.Column(db.DateTime, nullable=False)
    used: bool = db.Column(db.Boolean, default=False)

    def is_valid(self) -> bool:
        """Return True if the token has not been used and has not expired."""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        # Support both naive and aware datetimes stored in the DB
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return not self.used and now < expires

    def __repr__(self) -> str:
        return f'<PasswordResetToken user_id={self.user_id} used={self.used}>'
