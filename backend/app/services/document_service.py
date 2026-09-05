"""Service layer for document upload orchestration."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentListItem, DocumentUploadResponse
from app.services.document_processor import process_document
from app.services.document_storage import save_file, delete_file
from app.services.document_validator import validate_document


def _to_upload_response(doc: Document) -> DocumentUploadResponse:
    """Convert Document DB model to response schema."""
    return DocumentUploadResponse(
        document_id=doc.document_id,
        patient_id=doc.patient_id,
        filename=doc.filename,
        content_type=doc.content_type,
        file_size_bytes=doc.file_size_bytes,
        processing_status=doc.processing_status,
        page_count=doc.page_count,
        extracted_text=doc.extracted_text,
        error_message=doc.error_message,
        created_at=doc.created_at,
    )


def _to_list_item(doc: Document) -> DocumentListItem:
    """Convert Document DB model to list item schema."""
    return DocumentListItem(
        document_id=doc.document_id,
        patient_id=doc.patient_id,
        filename=doc.filename,
        content_type=doc.content_type,
        file_size_bytes=doc.file_size_bytes,
        processing_status=doc.processing_status,
        page_count=doc.page_count,
        created_at=doc.created_at,
    )


def upload_document(
    db: Session,
    patient_id: str,
    filename: str,
    content_type: str,
    file_content: bytes,
    upload_dir: Optional[str] = None,
) -> DocumentUploadResponse:
    """Validate, store, process, and persist a document upload.

    Pipeline:
    1. Validate file type, size, and magic bytes.
    2. Save file to disk (UUID-named).
    3. Extract text (PDF) or mark OCR_REQUIRED (image).
    4. Persist metadata + extracted text to SQLite.
    5. Return typed response.

    Raises:
        ValueError: If validation fails or patient not found.
    """
    # 1. Validate
    file_header = file_content[:16] if file_content else b""
    validation = validate_document(
        content_type=content_type,
        size_bytes=len(file_content),
        file_header=file_header,
    )
    if not validation.is_valid:
        raise ValueError(validation.error)

    # 2. Verify patient exists
    from app.models.patient import Patient

    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise ValueError(f"Patient with ID '{patient_id}' not found")

    # 3. Save to disk
    storage_path = save_file(
        file_content=file_content,
        original_filename=filename,
        upload_dir=upload_dir,
    )

    # 4. Process (text extraction)
    processing = process_document(
        file_content=file_content,
        content_type=content_type,
    )

    # 5. Persist metadata
    now = datetime.now(timezone.utc)
    document_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"

    db_document = Document(
        document_id=document_id,
        patient_id=patient_id,
        filename=filename,
        content_type=content_type,
        file_size_bytes=len(file_content),
        storage_path=storage_path,
        processing_status=processing.status,
        extracted_text=processing.extracted_text,
        page_count=processing.page_count,
        error_message=processing.error_message,
        created_at=now,
        updated_at=now,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return _to_upload_response(db_document)


def get_document(db: Session, document_id: str) -> Optional[DocumentUploadResponse]:
    """Retrieve a document by ID."""
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        return None
    return _to_upload_response(doc)


def list_patient_documents(db: Session, patient_id: str) -> list[DocumentListItem]:
    """List all documents for a patient."""
    docs = (
        db.query(Document)
        .filter(Document.patient_id == patient_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_to_list_item(doc) for doc in docs]
