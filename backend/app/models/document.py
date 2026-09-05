"""SQLAlchemy database model for Document."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.db.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class Document(Base):
    """Database model for storing uploaded medical documents and their processing state."""

    __tablename__ = "documents"

    document_id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)
    processing_status = Column(
        SAEnum(
            "PENDING",
            "TEXT_EXTRACTED",
            "OCR_REQUIRED",
            "PROCESSING_FAILED",
            name="processing_status_enum",
        ),
        nullable=False,
        default="PENDING",
    )
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
