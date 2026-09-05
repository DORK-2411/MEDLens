"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Returns service health status.

    No PHI, no secrets — safe for monitoring.
    """
    return {"status": "healthy", "service": "medlens-api"}
