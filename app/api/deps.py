"""Minimal dependencies for the temporary T03 inventory API."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.services.inventory import InventoryStore


def get_inventory_store(request: Request) -> InventoryStore:
    return request.app.state.inventory_store


def reject_repeated_query_parameters(request: Request) -> None:
    """Scalar query inputs must appear at most once, even with identical values."""
    seen: set[str] = set()
    errors = []
    for name, value in request.query_params.multi_items():
        if name in seen:
            errors.append(
                {
                    "type": "value_error",
                    "loc": ("query", name),
                    "msg": "Query parameter must not be repeated.",
                    "input": value,
                }
            )
        seen.add(name)
    if errors:
        raise RequestValidationError(errors)


def require_learning_environment(request: Request) -> None:
    """T03 writes have no identity checks; keep them disabled in production."""
    if request.app.state.settings.environment == "production":
        raise HTTPException(
            status_code=501,
            detail={
                "code": "inventory_administration_not_ready",
                "message": "Inventory administration requires T15-T16 authentication.",
            },
        )
