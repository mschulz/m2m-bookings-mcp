# app/routers/health.py

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", operation_id="health_check")
def health_check():
    """Check if the M2M Bookings API server is running and healthy."""
    return {"status": "ok", "service": "M2M Bookings API"}
