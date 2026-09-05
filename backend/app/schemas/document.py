"""Pydantic schemas for document upload and processing responses."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response returned after a document is uploaded and processed."""

    document_id: str = Field(description="Unique identifier for the document")
    patient_id: str = Field(description="Associated patient identifier")
    filename: str = Field(description="Original filename of the uploaded document")
    content_type: str = Field(description="MIME type of the uploaded file")
    file_size_bytes: int = Field(description="Size of the uploaded file in bytes")
    processing_status: Literal[
        "PENDING",
        "TEXT_EXTRACTED",
        "OCR_REQUIRED",
        "PROCESSING_FAILED",
    ] = Field(description="Current processing state of the document")
    page_count: Optional[int] = Field(
        default=None,
        description="Number of pages in the document (PDF only)",
    )
    extracted_text: Optional[str] = Field(
        default=None,
        description="Text extracted from the document (null if OCR required)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if processing failed",
    )
    created_at: datetime = Field(description="Upload timestamp")


class DocumentListItem(BaseModel):
    """Compact document summary for listing endpoints."""

    document_id: str
    patient_id: str
    filename: str
    content_type: str
    file_size_bytes: int
    processing_status: str
    page_count: Optional[int] = None
    created_at: datetime
