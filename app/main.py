"""ASGI entry point, versioned routers, and the public liveness endpoint."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import validation_error_response
from app.api.v1 import router
from app.core.config import Settings, get_settings
from app.services.inventory import InventoryStore


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application with fresh temporary inventory and validated settings."""
    if settings is None:
        settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        description=(
            "T03 learning API: inventory uses process-local memory. "
            "Inventory writes are unauthenticated in development/test and disabled "
            "in production until T15-T16. Auth and order routes return 501."
        ),
    )
    application.add_exception_handler(RequestValidationError, validation_error_response)
    application.state.settings = settings
    application.state.inventory_store = InventoryStore()
    application.include_router(router)

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
