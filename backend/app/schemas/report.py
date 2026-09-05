"""Diagnostic report schema grouping observations extracted from a clinical document."""

from typing import List
from pydantic import BaseModel, Field

from app.schemas.observation import Observation
from app.schemas.provenance import Provenance


class DiagnosticReport(BaseModel):
    """Structured clinical report containing observations extracted from a medical document."""

    report_id: str = Field(
        description="Unique identifier for the diagnostic report",
    )
    patient_id: str = Field(
        description="Identifier of the associated patient",
    )
    document_id: str = Field(
        description="Source document identifier",
    )
    observations: List[Observation] = Field(
        default_factory=list,
        description="List of observations extracted from this report",
    )
    provenance: Provenance = Field(
        description="Provenance metadata for the report extraction",
    )
