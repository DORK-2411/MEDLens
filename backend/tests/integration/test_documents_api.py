"""Integration tests for the document upload API endpoints."""

import io
import tempfile
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient


# ── Helper to create a patient first ───────────────────────────────


def _create_test_patient(client: TestClient) -> str:
    """Create a patient and return the patient_id."""
    resp = client.post(
        "/api/patients",
        json={
            "age": 45,
            "sex": "female",
            "symptoms": ["cough"],
            "conditions": [],
            "allergies": [],
            "medications": [],
        },
    )
    assert resp.status_code == 201
    return resp.json()["patient_id"]


def _make_simple_pdf(num_pages: int = 1) -> bytes:
    """Create a minimal valid PDF with blank pages."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ── Upload endpoint ────────────────────────────────────────────────


class TestDocumentUpload:
    def test_upload_pdf_success(self, client: TestClient):
        patient_id = _create_test_patient(client)
        pdf_content = _make_simple_pdf()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "app.services.document_service.save_file",
                wraps=lambda file_content, original_filename, upload_dir=None: __import__(
                    "app.services.document_storage", fromlist=["save_file"]
                ).save_file(file_content, original_filename, upload_dir=tmpdir),
            ):
                resp = client.post(
                    f"/api/patients/{patient_id}/documents",
                    files={"file": ("blood_test.pdf", pdf_content, "application/pdf")},
                )

        assert resp.status_code == 201
        data = resp.json()
        assert data["patient_id"] == patient_id
        assert data["filename"] == "blood_test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["processing_status"] in ("TEXT_EXTRACTED", "OCR_REQUIRED")
        assert data["document_id"].startswith("DOC-")
        assert data["file_size_bytes"] > 0

    def test_upload_png_returns_ocr_required(self, client: TestClient):
        patient_id = _create_test_patient(client)
        # Valid PNG magic bytes + minimal header
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "app.services.document_service.save_file",
                wraps=lambda file_content, original_filename, upload_dir=None: __import__(
                    "app.services.document_storage", fromlist=["save_file"]
                ).save_file(file_content, original_filename, upload_dir=tmpdir),
            ):
                resp = client.post(
                    f"/api/patients/{patient_id}/documents",
                    files={"file": ("scan.png", png_content, "image/png")},
                )

        assert resp.status_code == 201
        data = resp.json()
        assert data["processing_status"] == "OCR_REQUIRED"

    def test_upload_unsupported_type_rejected(self, client: TestClient):
        patient_id = _create_test_patient(client)
        resp = client.post(
            f"/api/patients/{patient_id}/documents",
            files={"file": ("data.zip", b"PK\x03\x04", "application/zip")},
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_upload_to_nonexistent_patient_rejected(self, client: TestClient):
        pdf_content = _make_simple_pdf()
        resp = client.post(
            "/api/patients/NONEXISTENT/documents",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]

    def test_upload_empty_file_rejected(self, client: TestClient):
        patient_id = _create_test_patient(client)
        resp = client.post(
            f"/api/patients/{patient_id}/documents",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_upload_magic_bytes_mismatch_rejected(self, client: TestClient):
        patient_id = _create_test_patient(client)
        # Claim PDF but send PNG bytes
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        resp = client.post(
            f"/api/patients/{patient_id}/documents",
            files={"file": ("fake.pdf", png_bytes, "application/pdf")},
        )
        assert resp.status_code == 400
        assert "magic bytes" in resp.json()["detail"].lower()


# ── List & Get endpoints ───────────────────────────────────────────


class TestDocumentListAndGet:
    def test_list_empty_documents(self, client: TestClient):
        patient_id = _create_test_patient(client)
        resp = client.get(f"/api/patients/{patient_id}/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_upload(self, client: TestClient):
        patient_id = _create_test_patient(client)
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "app.services.document_service.save_file",
                wraps=lambda file_content, original_filename, upload_dir=None: __import__(
                    "app.services.document_storage", fromlist=["save_file"]
                ).save_file(file_content, original_filename, upload_dir=tmpdir),
            ):
                client.post(
                    f"/api/patients/{patient_id}/documents",
                    files={"file": ("scan.png", png_content, "image/png")},
                )

        resp = client.get(f"/api/patients/{patient_id}/documents")
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 1
        assert docs[0]["filename"] == "scan.png"

    def test_get_document_by_id(self, client: TestClient):
        patient_id = _create_test_patient(client)
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "app.services.document_service.save_file",
                wraps=lambda file_content, original_filename, upload_dir=None: __import__(
                    "app.services.document_storage", fromlist=["save_file"]
                ).save_file(file_content, original_filename, upload_dir=tmpdir),
            ):
                upload_resp = client.post(
                    f"/api/patients/{patient_id}/documents",
                    files={"file": ("scan.png", png_content, "image/png")},
                )

        doc_id = upload_resp.json()["document_id"]
        resp = client.get(f"/api/patients/{patient_id}/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["document_id"] == doc_id

    def test_get_nonexistent_document_404(self, client: TestClient):
        patient_id = _create_test_patient(client)
        resp = client.get(f"/api/patients/{patient_id}/documents/DOC-NOTFOUND")
        assert resp.status_code == 404
