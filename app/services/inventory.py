"""Temporary process-local inventory storage, replaced by PostgreSQL in T13-T14."""

from datetime import UTC, datetime
from threading import Lock

from fastapi import HTTPException

from app.schemas.inventory import (
    InventoryCreate,
    InventoryPage,
    InventoryPatch,
    InventoryQuery,
    InventoryRead,
    InventoryReplace,
)


class InventoryStore:
    """One locked store per app; reload/restart clears all items."""

    def __init__(self) -> None:
        self._items: dict[int, InventoryRead] = {}
        self._sku_ids: dict[str, int] = {}
        self._next_id = 1
        self._lock = Lock()

    def _require(self, item_id: int) -> InventoryRead:
        item = self._items.get(item_id)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "inventory_item_not_found",
                    "message": "Inventory item was not found.",
                },
            )
        return item

    def create(self, body: InventoryCreate) -> InventoryRead:
        with self._lock:
            if body.sku in self._sku_ids:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "duplicate_sku",
                        "message": "An inventory item already uses this SKU.",
                    },
                )
            now = datetime.now(UTC)
            item = InventoryRead(
                **body.model_dump(),
                id=self._next_id,
                created_at=now,
                updated_at=now,
            )
            self._items[item.id] = item
            self._sku_ids[item.sku] = item.id
            self._next_id += 1
            return item

    def read(self, item_id: int) -> InventoryRead:
        with self._lock:
            item = self._require(item_id)
            if not item.is_active:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "inventory_item_not_found",
                        "message": "Inventory item was not found.",
                    },
                )
            return item

    def list(self, query: InventoryQuery) -> InventoryPage:
        with self._lock:
            items = [item for item in self._items.values() if item.is_active]
        if query.q is not None:
            term = query.q.casefold()
            items = [
                item
                for item in items
                if term in item.name.casefold() or term in item.sku.casefold()
            ]
        if query.in_stock is not None:
            wanted = query.in_stock == "true"
            items = [item for item in items if (item.stock > 0) == wanted]

        # Stable sorts preserve ascending IDs for equal names/prices in either direction.
        items.sort(key=lambda item: item.id)
        items.sort(
            key=lambda item: getattr(item, query.sort),
            reverse=query.direction == "desc",
        )
        return InventoryPage(
            items=items[query.offset : query.offset + query.limit],
            total=len(items),
            limit=query.limit,
            offset=query.offset,
        )

    def update(
        self, item_id: int, body: InventoryReplace | InventoryPatch
    ) -> InventoryRead:
        changes = body.model_dump(exclude_unset=isinstance(body, InventoryPatch))
        with self._lock:
            item = self._require(item_id)
            updated = item.model_copy(
                update={**changes, "updated_at": datetime.now(UTC)}
            )
            self._items[item_id] = updated
            return updated

    def deactivate(self, item_id: int) -> None:
        with self._lock:
            item = self._require(item_id)
            if item.is_active:
                self._items[item_id] = item.model_copy(
                    update={"is_active": False, "updated_at": datetime.now(UTC)}
                )
