from fastapi import FastAPI

from app.api.middleware import add_request_logging_middleware
from app.api.routes import health, reports
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )
    add_request_logging_middleware(app)
    app.include_router(health.router)
    app.include_router(reports.router)
    return app


app = create_app()
