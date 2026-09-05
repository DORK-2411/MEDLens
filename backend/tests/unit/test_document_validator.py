"""Unit tests for document_validator service."""

import pytest

from app.services.document_validator import (
    MAX_FILE_SIZE_BYTES,
    validate_content_type,
    validate_document,
    validate_file_size,
    validate_magic_bytes,
)


# ── validate_content_type ──────────────────────────────────────────


class TestValidateContentType:
    def test_pdf_accepted(self):
        result = validate_content_type("application/pdf")
        assert result.is_valid is True
        assert result.error is None

    def test_png_accepted(self):
        result = validate_content_type("image/png")
        assert result.is_valid is True

    def test_jpeg_accepted(self):
        result = validate_content_type("image/jpeg")
        assert result.is_valid is True

    def test_unsupported_type_rejected(self):
        result = validate_content_type("application/zip")
        assert result.is_valid is False
        assert "Unsupported file type" in result.error

    def test_octet_stream_rejected(self):
        result = validate_content_type("application/octet-stream")
        assert result.is_valid is False

    def test_text_plain_rejected(self):
        result = validate_content_type("text/plain")
        assert result.is_valid is False


# ── validate_file_size ─────────────────────────────────────────────


class TestValidateFileSize:
    def test_normal_size_accepted(self):
        result = validate_file_size(1024)
        assert result.is_valid is True

    def test_max_size_accepted(self):
        result = validate_file_size(MAX_FILE_SIZE_BYTES)
        assert result.is_valid is True

    def test_oversized_rejected(self):
        result = validate_file_size(MAX_FILE_SIZE_BYTES + 1)
        assert result.is_valid is False
        assert "exceeds maximum" in result.error

    def test_empty_file_rejected(self):
        result = validate_file_size(0)
        assert result.is_valid is False
        assert "empty" in result.error

    def test_negative_size_rejected(self):
        result = validate_file_size(-1)
        assert result.is_valid is False


# ── validate_magic_bytes ───────────────────────────────────────────


class TestValidateMagicBytes:
    def test_pdf_magic_valid(self):
        header = b"%PDF-1.4 rest of file..."
        result = validate_magic_bytes("application/pdf", header)
        assert result.is_valid is True

    def test_pdf_magic_invalid(self):
        header = b"\x89PNG\r\n\x1a\n"
        result = validate_magic_bytes("application/pdf", header)
        assert result.is_valid is False
        assert "magic bytes mismatch" in result.error

    def test_png_magic_valid(self):
        header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        result = validate_magic_bytes("image/png", header)
        assert result.is_valid is True

    def test_jpeg_magic_valid(self):
        header = b"\xff\xd8\xff\xe0" + b"\x00" * 12
        result = validate_magic_bytes("image/jpeg", header)
        assert result.is_valid is True

    def test_jpeg_magic_invalid(self):
        header = b"%PDF-1.4"
        result = validate_magic_bytes("image/jpeg", header)
        assert result.is_valid is False

    def test_unknown_type_skips_check(self):
        header = b"anything"
        result = validate_magic_bytes("application/unknown", header)
        assert result.is_valid is True


# ── validate_document (composite) ─────────────────────────────────


class TestValidateDocument:
    def test_valid_pdf(self):
        header = b"%PDF-1.4" + b"\x00" * 8
        result = validate_document("application/pdf", 1024, header)
        assert result.is_valid is True

    def test_valid_png(self):
        header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        result = validate_document("image/png", 2048, header)
        assert result.is_valid is True

    def test_invalid_type_fails_first(self):
        result = validate_document("text/html", 1024, b"<html>")
        assert result.is_valid is False
        assert "Unsupported file type" in result.error

    def test_oversized_fails(self):
        header = b"%PDF-1.4" + b"\x00" * 8
        result = validate_document("application/pdf", MAX_FILE_SIZE_BYTES + 1, header)
        assert result.is_valid is False
        assert "exceeds maximum" in result.error

    def test_magic_mismatch_fails(self):
        # Declared PDF but content is PNG
        header = b"\x89PNG\r\n\x1a\n"
        result = validate_document("application/pdf", 1024, header)
        assert result.is_valid is False
        assert "magic bytes mismatch" in result.error
