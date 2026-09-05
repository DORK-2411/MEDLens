"""Conflict schema representing discrepancies between patient-reported data and extracted history."""

from datetime import datetime
from pydantic import BaseModel, Field


class Conflict(BaseModel):
    """Represents a discrepancy detected between patient-reported info and clinical document history."""

    field: str = Field(
        description="Field or category where the discrepancy was found (e.g. 'allergies', 'medications')",
    )
    patient_reported_value: str = Field(
        description="Value or assertion reported by the patient",
    )
    extracted_value: str = Field(
        description="Conflicting value found in extracted clinical documentation",
    )
    source_document_id: str = Field(
        description="Document ID of the source report where the conflicting value originated",
    )
    detected_at: datetime = Field(
        description="Timestamp when the conflict was detected",
    )
