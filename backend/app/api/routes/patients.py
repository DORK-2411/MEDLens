"""FastAPI route handlers for patient intake and record management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.patient import PatientCreate, PatientRecord, PatientUpdate
from app.services.patient_service import (
    create_patient,
    delete_patient,
    get_patient,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post(
    "",
    response_model=PatientRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Create patient intake record",
)
def create_patient_route(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
) -> PatientRecord:
    """Create a new patient intake record."""
    try:
        return create_patient(db=db, patient_in=patient_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.get(
    "/{patient_id}",
    response_model=PatientRecord,
    summary="Get patient record by ID",
)
def get_patient_route(
    patient_id: str,
    db: Session = Depends(get_db),
) -> PatientRecord:
    """Retrieve an existing patient record."""
    patient = get_patient(db=db, patient_id=patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found",
        )
    return patient


@router.put(
    "/{patient_id}",
    response_model=PatientRecord,
    summary="Update patient record",
)
def update_patient_route(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
) -> PatientRecord:
    """Update demographic or clinical information for an existing patient."""
    updated = update_patient(db=db, patient_id=patient_id, patient_update=patient_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found",
        )
    return updated


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete patient record",
)
def delete_patient_route(
    patient_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a patient intake record by ID."""
    deleted = delete_patient(db=db, patient_id=patient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found",
        )
    return {"status": "deleted", "patient_id": patient_id}
