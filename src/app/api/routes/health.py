from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.health import HealthCheck, RootInfo

router = APIRouter(tags=["health"])


@router.get("/", response_model=RootInfo)
def root_info(settings: Annotated[Settings, Depends(get_settings)]) -> RootInfo:
    return RootInfo(
        service=settings.app_name,
        environment=settings.environment,
        description="FastAPI service for matching resumes with vacancies.",
        docs_url="/docs",
        health_url="/health",
    )


@router.get("/health", response_model=HealthCheck)
def health_check(settings: Annotated[Settings, Depends(get_settings)]) -> HealthCheck:
    return HealthCheck(status="ok", service=settings.app_name, environment=settings.environment)
