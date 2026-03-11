"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}
