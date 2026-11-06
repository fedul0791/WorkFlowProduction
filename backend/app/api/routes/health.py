from fastapi import APIRouter, HTTPException, status

from app.db.session import check_database
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Check API and database health")
def health_check() -> HealthResponse:
    try:
        check_database()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "database": "unavailable"},
        ) from exc

    return HealthResponse(status="ok", database="connected")
