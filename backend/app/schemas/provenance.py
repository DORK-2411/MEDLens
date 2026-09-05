"""Provenance tracking schema for data origin, confidence, and edit history."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Provenance(BaseModel):
    """Tracks the origin, model confidence, and human audit trail of a data field."""

    source: Literal["user_provided", "ai_extracted", "ai_generated"]
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score between 0.0 and 1.0 (applicable to AI sources)",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Identifier of source document report if extracted",
    )
    extracted_at: datetime = Field(
        description="Timestamp when the data was initially extracted or provided",
    )
    edited_by: Optional[str] = Field(
        default=None,
        description="Identifier of reviewer/user who modified or verified this field",
    )
    edited_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the most recent human edit/verification",
    )
