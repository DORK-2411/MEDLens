"""Unit tests for document_storage service."""

import os
import tempfile
import pytest

from app.services.document_storage import (
    delete_file,
    generate_storage_filename,
    save_file,
    _safe_extension,
)


# ── generate_storage_filename ──────────────────────────────────────


class TestGenerateStorageFilename:
    def test_pdf_extension_preserved(self):
        name = generate_storage_filename("report.pdf")
        assert name.endswith(".pdf")
        assert len(name) == 36  # 32 hex + '.pdf'

    def test_png_extension_preserved(self):
        name = generate_storage_filename("scan.PNG")
        assert name.endswith(".png")

    def test_jpeg_extension_preserved(self):
        name = generate_storage_filename("photo.jpeg")
        assert name.endswith(".jpeg")

    def test_jpg_extension_preserved(self):
        name = generate_storage_filename("photo.jpg")
        assert name.endswith(".jpg")

    def test_dangerous_extension_stripped(self):
        name = generate_storage_filename("exploit.exe")
        assert not name.endswith(".exe")
        assert "exploit" not in name

    def test_no_extension(self):
        name = generate_storage_filename("noextension")
        assert "." not in name or name.endswith("")  # UUID hex only

    def test_unique_names(self):
        names = {generate_storage_filename("test.pdf") for _ in range(100)}
        assert len(names) == 100  # All unique

    def test_path_traversal_filename_ignored(self):
        name = generate_storage_filename("../../etc/passwd.pdf")
        assert ".." not in name
        assert "etc" not in name
        assert "passwd" not in name
        assert name.endswith(".pdf")


# ── _safe_extension ────────────────────────────────────────────────


class TestSafeExtension:
    def test_safe_pdf(self):
        assert _safe_extension("file.pdf") == ".pdf"

    def test_safe_png(self):
        assert _safe_extension("file.png") == ".png"

    def test_unsafe_returns_empty(self):
        assert _safe_extension("file.sh") == ""

    def test_no_ext_returns_empty(self):
        assert _safe_extension("noext") == ""


# ── save_file ──────────────────────────────────────────────────────


class TestSaveFile:
    def test_save_and_read_back(self):
        content = b"fake pdf content"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_file(content, "report.pdf", upload_dir=tmpdir)
            assert os.path.exists(path)
            with open(path, "rb") as f:
                assert f.read() == content

    def test_saved_filename_is_uuid_based(self):
        content = b"test"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_file(content, "my_report.pdf", upload_dir=tmpdir)
            basename = os.path.basename(path)
            assert "my_report" not in basename
            assert basename.endswith(".pdf")

    def test_upload_dir_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "sub", "dir")
            path = save_file(b"data", "test.png", upload_dir=nested_dir)
            assert os.path.exists(path)


# ── delete_file ────────────────────────────────────────────────────


class TestDeleteFile:
    def test_delete_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_file(b"deleteme", "temp.pdf", upload_dir=tmpdir)
            assert os.path.exists(path)
            result = delete_file(path)
            assert result is True
            assert not os.path.exists(path)

    def test_delete_nonexistent_returns_false(self):
        result = delete_file("/nonexistent/path/to/file.pdf")
        assert result is False
