"""FastAPI route handlers for document upload and retrieval."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import DocumentListItem, DocumentUploadResponse
from app.services.document_service import (
    get_document,
    list_patient_documents,
    upload_document,
)

router = APIRouter(prefix="/patients/{patient_id}/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a medical document for a patient",
)
async def upload_document_route(
    patient_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a PDF or image medical document for processing.

    Accepts: application/pdf, image/png, image/jpeg
    Max size: 20 MB

    Pipeline: validate → store → extract text → persist metadata.
    """
    file_content = await file.read()

    content_type = file.content_type or "application/octet-stream"

    try:
        result = upload_document(
            db=db,
            patient_id=patient_id,
            filename=file.filename or "unnamed",
            content_type=content_type,
            file_content=file_content,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return result


@router.get(
    "",
    response_model=list[DocumentListItem],
    summary="List documents for a patient",
)
def list_documents_route(
    patient_id: str,
    db: Session = Depends(get_db),
) -> list[DocumentListItem]:
    """List all uploaded documents for a given patient."""
    return list_patient_documents(db=db, patient_id=patient_id)


@router.get(
    "/{document_id}",
    response_model=DocumentUploadResponse,
    summary="Get document details by ID",
)
def get_document_route(
    patient_id: str,
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """Retrieve full details of a specific document."""
    doc = get_document(db=db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found",
        )
    if doc.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' does not belong to patient '{patient_id}'",
        )
    return doc
