"""Service layer for patient intake operations."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientRecord, PatientUpdate


def _to_patient_record(patient: Patient) -> PatientRecord:
    """Convert Patient database model to PatientRecord schema."""
    return PatientRecord(
        patient_id=patient.patient_id,
        age=patient.age,
        sex=patient.sex,
        notes=patient.notes,
        symptoms=list(patient.symptoms or []),
        conditions=list(patient.conditions or []),
        allergies=list(patient.allergies or []),
        medications=list(patient.medications or []),
        reports=[],
        audit_log=[],
    )


def create_patient(db: Session, patient_in: PatientCreate) -> PatientRecord:
    """Create a new patient record in SQLite."""
    # Generate patient_id if not provided
    patient_id = patient_in.patient_id
    if not patient_id:
        patient_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"

    # Check for existing patient with this ID
    existing = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if existing:
        raise ValueError(f"Patient with ID '{patient_id}' already exists")

    now = datetime.now(timezone.utc)
    db_patient = Patient(
        patient_id=patient_id,
        age=patient_in.age,
        sex=patient_in.sex,
        symptoms=patient_in.symptoms,
        conditions=patient_in.conditions,
        allergies=patient_in.allergies,
        medications=patient_in.medications,
        notes=patient_in.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    return _to_patient_record(db_patient)


def get_patient(db: Session, patient_id: str) -> Optional[PatientRecord]:
    """Retrieve a patient record by ID."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return None
    return _to_patient_record(patient)


def update_patient(
    db: Session, patient_id: str, patient_update: PatientUpdate
) -> Optional[PatientRecord]:
    """Update an existing patient record."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return None

    update_data = patient_update.model_dump(exclude_unset=True)

    if "age" in update_data:
        patient.age = update_data["age"]
    if "sex" in update_data:
        patient.sex = update_data["sex"]
    if "notes" in update_data:
        patient.notes = update_data["notes"]
    if "symptoms" in update_data and update_data["symptoms"] is not None:
        patient.symptoms = update_data["symptoms"]
    if "conditions" in update_data and update_data["conditions"] is not None:
        patient.conditions = update_data["conditions"]
    if "allergies" in update_data and update_data["allergies"] is not None:
        patient.allergies = update_data["allergies"]
    if "medications" in update_data and update_data["medications"] is not None:
        patient.medications = update_data["medications"]

    patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(patient)

    return _to_patient_record(patient)


def delete_patient(db: Session, patient_id: str) -> bool:
    """Delete a patient record by ID."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return False

    db.delete(patient)
    db.commit()
    return True
