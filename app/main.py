"""ASGI application entry point and the public liveness endpoint."""

from fastapi import FastAPI

from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application with validated configuration."""
    if settings is None:
        settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )

    @application.get(
        "/health",
        tags=["Health"],
        summary="Check application liveness",
        description="Confirms the app responds; does not check external resources.",
    )
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
