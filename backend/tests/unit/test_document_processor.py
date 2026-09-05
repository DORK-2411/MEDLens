"""Unit tests for document_processor service."""

import io
import pytest

from app.services.document_processor import process_document


# ── Image processing ───────────────────────────────────────────────


class TestImageProcessing:
    def test_png_returns_ocr_required(self):
        result = process_document(b"\x89PNG\r\n\x1a\n", "image/png")
        assert result.status == "OCR_REQUIRED"
        assert result.page_count == 1
        assert result.extracted_text is None
        assert result.error_message is None

    def test_jpeg_returns_ocr_required(self):
        result = process_document(b"\xff\xd8\xff\xe0", "image/jpeg")
        assert result.status == "OCR_REQUIRED"
        assert result.page_count == 1
        assert result.extracted_text is None

    def test_unsupported_type_fails(self):
        result = process_document(b"data", "application/zip")
        assert result.status == "PROCESSING_FAILED"
        assert "Unsupported content type" in result.error_message


# ── PDF processing ─────────────────────────────────────────────────


class TestPdfProcessing:
    def _make_pdf_with_text(self, text: str) -> bytes:
        """Create a minimal PDF with embedded text using pypdf."""
        from pypdf import PdfWriter
        from pypdf._page import PageObject
        from pypdf.generic import (
            ArrayObject,
            DictionaryObject,
            NameObject,
            NumberObject,
            TextStringObject,
            ContentStream,
        )

        writer = PdfWriter()

        # Create a minimal page with text content
        page = PageObject.create_blank_page(width=612, height=792)

        # Build a simple content stream with text
        content = f"BT /F1 12 Tf 100 700 Td ({text}) Tj ET"
        page[NameObject("/Contents")] = writer._add_object(
            ContentStream(None, b"")
        )

        # Add a font resource
        font_dict = DictionaryObject()
        font_dict[NameObject("/Type")] = NameObject("/Font")
        font_dict[NameObject("/Subtype")] = NameObject("/Type1")
        font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")

        fonts = DictionaryObject()
        fonts[NameObject("/F1")] = writer._add_object(font_dict)

        resources = DictionaryObject()
        resources[NameObject("/Font")] = fonts
        page[NameObject("/Resources")] = resources

        writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    def _make_simple_pdf(self, num_pages: int = 1) -> bytes:
        """Create a minimal valid PDF with blank pages."""
        from pypdf import PdfWriter

        writer = PdfWriter()
        for _ in range(num_pages):
            writer.add_blank_page(width=612, height=792)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    def test_blank_pdf_returns_ocr_required(self):
        """A PDF with no text content should be marked OCR_REQUIRED."""
        pdf_bytes = self._make_simple_pdf(num_pages=2)
        result = process_document(pdf_bytes, "application/pdf")
        assert result.status == "OCR_REQUIRED"
        assert result.page_count == 2
        assert result.extracted_text is None

    def test_multi_page_blank_pdf(self):
        pdf_bytes = self._make_simple_pdf(num_pages=5)
        result = process_document(pdf_bytes, "application/pdf")
        assert result.status == "OCR_REQUIRED"
        assert result.page_count == 5

    def test_invalid_pdf_returns_processing_failed(self):
        """Corrupted PDF content should return PROCESSING_FAILED."""
        result = process_document(b"%PDF-1.4 corrupted garbage", "application/pdf")
        assert result.status == "PROCESSING_FAILED"
        assert result.error_message is not None
        assert "PDF processing failed" in result.error_message

    def test_empty_bytes_pdf_fails(self):
        result = process_document(b"", "application/pdf")
        assert result.status == "PROCESSING_FAILED"
