"""Supplier model for financial module."""
from datetime import datetime, timezone
from app import db


class Supplier(db.Model):
    """Represents a supplier/vendor for financial transactions."""

    __tablename__ = 'suppliers'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(150), nullable=False, unique=True)
    cnpj: str = db.Column(db.String(20), nullable=True)
    contact_person: str = db.Column(db.String(100), nullable=True)
    email: str = db.Column(db.String(100), nullable=True)
    phone: str = db.Column(db.String(20), nullable=True)
    address: str = db.Column(db.Text, nullable=True)
    city: str = db.Column(db.String(100), nullable=True)
    state: str = db.Column(db.String(2), nullable=True)
    status: str = db.Column(db.String(20), default='active', nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f'<Supplier name={self.name}>'
