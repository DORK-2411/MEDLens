"""Patient record schemas for intake, update, and clinical history."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.audit import AuditLog
from app.schemas.report import DiagnosticReport


class PatientBase(BaseModel):
    """Base schema for patient intake data."""

    age: Optional[int] = Field(
        default=None,
        ge=0,
        description="Patient age in years (must be non-negative)",
    )
    sex: Optional[str] = Field(
        default=None,
        description="Biological sex or gender identity",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free-text clinical notes or additional patient remarks",
    )
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of self-reported symptoms",
    )
    conditions: List[str] = Field(
        default_factory=list,
        description="List of existing or diagnosed conditions",
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of known allergies",
    )
    medications: List[str] = Field(
        default_factory=list,
        description="List of current medications",
    )

    @field_validator("sex", "notes", mode="before")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

    @field_validator("symptoms", "conditions", "allergies", "medications", mode="before")
    @classmethod
    def clean_lists(cls, v: Optional[List[str]]) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            cleaned_items = []
            for item in v:
                if isinstance(item, str):
                    s = item.strip()
                    if s:
                        cleaned_items.append(s)
            return cleaned_items
        return []


class PatientCreate(PatientBase):
    """Schema for creating a new patient record."""

    patient_id: Optional[str] = Field(
        default=None,
        description="Optional custom patient ID. If omitted, one will be generated.",
    )

    @field_validator("patient_id", mode="before")
    @classmethod
    def validate_patient_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = str(v).strip()
            if not s:
                raise ValueError("patient_id cannot be empty or whitespace only")
            return s
        return None


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient record."""

    age: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated age in years (must be non-negative)",
    )
    sex: Optional[str] = None
    notes: Optional[str] = None
    symptoms: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None

    @field_validator("sex", "notes", mode="before")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

    @field_validator("symptoms", "conditions", "allergies", "medications", mode="before")
    @classmethod
    def clean_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, list):
            cleaned_items = []
            for item in v:
                if isinstance(item, str):
                    s = item.strip()
                    if s:
                        cleaned_items.append(s)
            return cleaned_items
        return []


class PatientRecord(BaseModel):
    """Aggregated patient record containing demographic intake, reports, and audit logs."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: str = Field(
        description="Unique identifier for the patient",
    )
    age: Optional[int] = Field(
        default=None,
        ge=0,
        description="Patient age in years (must be non-negative)",
    )
    sex: Optional[str] = Field(
        default=None,
        description="Biological sex or gender identity",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free-text clinical notes or additional patient remarks",
    )
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of self-reported or observed symptoms",
    )
    conditions: List[str] = Field(
        default_factory=list,
        description="List of diagnosed or existing medical conditions",
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of known allergies or adverse reactions",
    )
    medications: List[str] = Field(
        default_factory=list,
        description="List of current medications",
    )
    reports: List[DiagnosticReport] = Field(
        default_factory=list,
        description="Structured diagnostic reports associated with the patient",
    )
    audit_log: List[AuditLog] = Field(
        default_factory=list,
        description="Audit entries capturing human edits and verifications",
    )
