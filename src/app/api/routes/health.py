from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.health import HealthCheck

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
def health_check(settings: Annotated[Settings, Depends(get_settings)]) -> HealthCheck:
    return HealthCheck(status="ok", service=settings.app_name, environment=settings.environment)
