"""API routes package."""

from app.api.routes.health import router as health_router
from app.api.routes.patients import router as patients_router

__all__ = ["health_router", "patients_router"]
