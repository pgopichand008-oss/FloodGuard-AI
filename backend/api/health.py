from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint confirming backend operational status."""
    return {
        "status": "ok",
        "message": "FloodGuard backend is running",
        "version": "0.1.0"
    }
