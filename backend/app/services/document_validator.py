"""Document validation service — file type, size, and magic-byte checks."""

from dataclasses import dataclass
from typing import Optional

# Maximum upload size: 20 MB
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

# Magic byte signatures for file type verification
MAGIC_BYTES = {
    "application/pdf": b"%PDF",
    "image/png": b"\x89PNG",
    "image/jpeg": b"\xff\xd8\xff",
}


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a file validation check."""

    is_valid: bool
    error: Optional[str] = None


def validate_content_type(content_type: str) -> ValidationResult:
    """Validate that the MIME type is in the allowlist."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        return ValidationResult(
            is_valid=False,
            error=(
                f"Unsupported file type: '{content_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            ),
        )
    return ValidationResult(is_valid=True)


def validate_file_size(size_bytes: int) -> ValidationResult:
    """Validate that the file does not exceed the maximum upload size."""
    if size_bytes <= 0:
        return ValidationResult(is_valid=False, error="File is empty (0 bytes)")
    if size_bytes > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        return ValidationResult(
            is_valid=False,
            error=f"File size ({size_bytes} bytes) exceeds maximum allowed ({max_mb:.0f} MB)",
        )
    return ValidationResult(is_valid=True)


def validate_magic_bytes(content_type: str, file_header: bytes) -> ValidationResult:
    """Validate that the file header matches the expected magic bytes for its MIME type."""
    expected = MAGIC_BYTES.get(content_type)
    if expected is None:
        # No magic bytes registered for this type — skip check
        return ValidationResult(is_valid=True)
    if not file_header.startswith(expected):
        return ValidationResult(
            is_valid=False,
            error=f"File content does not match declared type '{content_type}' (magic bytes mismatch)",
        )
    return ValidationResult(is_valid=True)


def validate_document(
    content_type: str,
    size_bytes: int,
    file_header: bytes,
) -> ValidationResult:
    """Run all validation checks on an uploaded document.

    Returns the first failing ValidationResult, or a passing result if all checks pass.
    """
    for check in [
        validate_content_type(content_type),
        validate_file_size(size_bytes),
        validate_magic_bytes(content_type, file_header),
    ]:
        if not check.is_valid:
            return check
    return ValidationResult(is_valid=True)
