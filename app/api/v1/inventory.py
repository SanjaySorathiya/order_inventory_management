"""Working inventory CRUD and validated catalog queries for T03 and T07."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.api.deps import (
    get_inventory_store,
    reject_repeated_query_parameters,
    require_learning_environment,
)
from app.schemas.inventory import (
    MAX_INT64,
    InventoryCreate,
    InventoryPage,
    InventoryPatch,
    InventoryQuery,
    InventoryRead,
    InventoryReplace,
)
from app.services.inventory import InventoryStore

router = APIRouter(prefix="/inventory", tags=["Inventory"])
ItemId = Annotated[int, Path(gt=0, le=MAX_INT64)]
Store = Annotated[InventoryStore, Depends(get_inventory_store)]
learning_write = [Depends(require_learning_environment)]

NOT_FOUND = {
    "description": "No active inventory item has this identifier.",
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "code": "inventory_item_not_found",
                    "message": "Inventory item was not found.",
                }
            }
        }
    },
}
NOT_READY = {
    "description": (
        "Inventory administration is disabled in production until T15-T16 "
        "authentication exists."
    ),
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "code": "inventory_administration_not_ready",
                    "message": "Inventory administration requires T15-T16 authentication.",
                }
            }
        }
    },
}
DUPLICATE_SKU = {
    "description": "Another inventory item already uses this SKU.",
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "code": "duplicate_sku",
                    "message": "An inventory item already uses this SKU.",
                }
            }
        }
    },
}


@router.get(
    "",
    response_model=InventoryPage,
    summary="List active inventory",
    description=(
        "Filters, sorts, and paginates active items. Requesting "
        "`include_inactive=true` is refused until admin authentication exists (T16)."
    ),
    responses={
        403: {
            "description": "Inactive inventory was requested without admin authentication.",
        }
    },
    dependencies=[Depends(reject_repeated_query_parameters)],
)
def list_inventory(
    query: Annotated[InventoryQuery, Query()], store: Store
) -> InventoryPage:
    """Filter first, sort next, then paginate; inactive access awaits admin auth."""
    if query.include_inactive == "true":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden",
                "message": "Inactive inventory requires an authenticated admin.",
            },
        )
    return store.list(query)


@router.get(
    "/{item_id}",
    response_model=InventoryRead,
    summary="Get one active inventory item",
    description="Returns the public representation of an active item by ID.",
    responses={404: NOT_FOUND},
)
def read_inventory(item_id: ItemId, store: Store) -> InventoryRead:
    return store.read(item_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=InventoryRead,
    summary="Create an inventory item",
    description=(
        "Creates an item with an immutable SKU. Returns 201 with a `Location` "
        "header. Disabled in production until authentication exists."
    ),
    responses={409: DUPLICATE_SKU, 501: NOT_READY},
    dependencies=learning_write,
)
def create_inventory(
    body: InventoryCreate, response: Response, store: Store
) -> InventoryRead:
    item = store.create(body)
    response.headers["Location"] = f"/api/v1/inventory/{item.id}"
    return item


@router.put(
    "/{item_id}",
    response_model=InventoryRead,
    summary="Replace an inventory item",
    description=(
        "Replaces every mutable field of an existing item. Never creates an item; "
        "SKU and identifiers are immutable."
    ),
    responses={404: NOT_FOUND, 501: NOT_READY},
    dependencies=learning_write,
)
def replace_inventory(
    item_id: ItemId, body: InventoryReplace, store: Store
) -> InventoryRead:
    """Replace all mutable fields of an existing item; never creates an item."""
    return store.update(item_id, body)


@router.patch(
    "/{item_id}",
    response_model=InventoryRead,
    summary="Update selected inventory fields",
    description=(
        "Changes only supplied fields. Explicit `null` clears only `description`; "
        "an empty body is rejected with 422."
    ),
    responses={404: NOT_FOUND, 501: NOT_READY},
    dependencies=learning_write,
)
def patch_inventory(
    item_id: ItemId, body: InventoryPatch, store: Store
) -> InventoryRead:
    """Only explicitly supplied fields change; nullable description can be cleared."""
    return store.update(item_id, body)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Deactivate an inventory item",
    description=(
        "Deactivates the item while preserving its SKU and stock. Returns an empty "
        "204 response; repeated calls are idempotent."
    ),
    responses={404: NOT_FOUND, 501: NOT_READY},
    dependencies=learning_write,
)
def delete_inventory(item_id: ItemId, store: Store) -> Response:
    """Deactivate while preserving the SKU and stock; repeated calls are idempotent."""
    store.deactivate(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
