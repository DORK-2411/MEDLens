"""Document storage service — safe file persistence with path-traversal prevention."""

import os
import uuid
from pathlib import Path
from typing import Optional

# Default upload directory — relative to project root
DEFAULT_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads",
)


def _get_upload_dir(upload_dir: Optional[str] = None) -> Path:
    """Resolve and ensure the upload directory exists."""
    directory = Path(upload_dir) if upload_dir else Path(DEFAULT_UPLOAD_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory.resolve()


def _safe_extension(filename: str) -> str:
    """Extract a safe file extension from the original filename."""
    # Only allow known safe extensions
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    _, ext = os.path.splitext(filename.lower())
    if ext in allowed_extensions:
        return ext
    return ""


def generate_storage_filename(original_filename: str) -> str:
    """Generate a collision-free, safe filename using UUID.

    The original filename is never used as-is to prevent
    path traversal and injection attacks.
    """
    ext = _safe_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


def save_file(
    file_content: bytes,
    original_filename: str,
    upload_dir: Optional[str] = None,
) -> str:
    """Save file content to the upload directory and return the absolute storage path.

    Security:
    - Original filename is discarded; a UUID-based name is generated.
    - Final resolved path is verified to be within the upload directory.

    Raises:
        ValueError: If the resolved path escapes the upload directory (path traversal).
        OSError: If the file cannot be written.
    """
    directory = _get_upload_dir(upload_dir)
    safe_name = generate_storage_filename(original_filename)
    target_path = (directory / safe_name).resolve()

    # Path traversal guard — ensure target is inside upload dir
    if not str(target_path).startswith(str(directory)):
        raise ValueError("Path traversal detected: file path escapes upload directory")

    target_path.write_bytes(file_content)
    return str(target_path)


def delete_file(storage_path: str) -> bool:
    """Delete a stored file. Returns True if deleted, False if not found."""
    path = Path(storage_path)
    if path.exists() and path.is_file():
        path.unlink()
        return True
    return False
