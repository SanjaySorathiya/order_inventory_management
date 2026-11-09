"""Working inventory CRUD and validated catalog queries for T03."""

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


@router.get("", dependencies=[Depends(reject_repeated_query_parameters)])
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


@router.get("/{item_id}")
def read_inventory(item_id: ItemId, store: Store) -> InventoryRead:
    return store.read(item_id)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=learning_write)
def create_inventory(
    body: InventoryCreate, response: Response, store: Store
) -> InventoryRead:
    item = store.create(body)
    response.headers["Location"] = f"/api/v1/inventory/{item.id}"
    return item


@router.put("/{item_id}", dependencies=learning_write)
def replace_inventory(
    item_id: ItemId, body: InventoryReplace, store: Store
) -> InventoryRead:
    """Replace all mutable fields of an existing item; never creates an item."""
    return store.update(item_id, body)


@router.patch("/{item_id}", dependencies=learning_write)
def patch_inventory(
    item_id: ItemId, body: InventoryPatch, store: Store
) -> InventoryRead:
    """Only explicitly supplied fields change; nullable description can be cleared."""
    return store.update(item_id, body)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=learning_write,
)
def delete_inventory(item_id: ItemId, store: Store) -> Response:
    """Deactivate while preserving the SKU and stock; repeated calls are idempotent."""
    store.deactivate(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
