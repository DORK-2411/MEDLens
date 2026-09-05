"""Document processing service — text extraction from PDFs, image classification.

Architecture:
- PDFs: Extract embedded text using PyPDF2. If no text found, mark OCR_REQUIRED.
- Images (PNG/JPEG): Always mark OCR_REQUIRED (OCR not implemented in Phase 4).
- Never guesses or fabricates content. Missing text → null.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessingResult:
    """Outcome of processing a document for text extraction."""

    status: str  # TEXT_EXTRACTED | OCR_REQUIRED | PROCESSING_FAILED
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None


IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}


def process_document(
    file_content: bytes,
    content_type: str,
) -> ProcessingResult:
    """Process a document and attempt text extraction.

    - PDFs: Uses PyPDF2 to extract embedded text from all pages.
    - Images: Marked as OCR_REQUIRED (no OCR engine in this phase).
    - Failures are caught and returned as PROCESSING_FAILED, never raised.
    """
    if content_type in IMAGE_CONTENT_TYPES:
        return ProcessingResult(
            status="OCR_REQUIRED",
            page_count=1,
        )

    if content_type == "application/pdf":
        return _process_pdf(file_content)

    return ProcessingResult(
        status="PROCESSING_FAILED",
        error_message=f"Unsupported content type for processing: {content_type}",
    )


def _process_pdf(file_content: bytes) -> ProcessingResult:
    """Extract text from a PDF using PyPDF2."""
    try:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_content))
        page_count = len(reader.pages)

        text_parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

        full_text = "\n\n".join(text_parts).strip()

        if full_text:
            return ProcessingResult(
                status="TEXT_EXTRACTED",
                extracted_text=full_text,
                page_count=page_count,
            )
        else:
            # PDF exists but has no extractable text (scanned document)
            return ProcessingResult(
                status="OCR_REQUIRED",
                page_count=page_count,
            )

    except ImportError:
        return ProcessingResult(
            status="PROCESSING_FAILED",
            error_message="pypdf library is not installed",
        )
    except Exception as exc:
        return ProcessingResult(
            status="PROCESSING_FAILED",
            error_message=f"PDF processing failed: {str(exc)}",
        )
