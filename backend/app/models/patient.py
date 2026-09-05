"""SQLAlchemy database model for Patient."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

from app.db.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class Patient(Base):
    """Database model for storing patient intake data."""

    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, index=True)
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    symptoms = Column(JSON, default=list, nullable=False)
    conditions = Column(JSON, default=list, nullable=False)
    allergies = Column(JSON, default=list, nullable=False)
    medications = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
