import logging

from fastapi import FastAPI

from app.config import get_settings
from app.errors.handlers import register_error_handlers
from app.routers import auth, health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Backend API for a finance dashboard system with "
            "role-based acess control, financial record managemnet, "
            "and summary anlytics."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register global error handlers
    register_error_handlers(app)

    # Register routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")

    logger.info(f"Applications '{settings.APP_NAME}' initialized")
    return app


app = create_app()
