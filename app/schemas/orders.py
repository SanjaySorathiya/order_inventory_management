"""Order request and response schemas for checkout and status workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.inventory import MAX_INT64, Name, PositiveId, Sku

MAX_LINE_QUANTITY = 10_000
Quantity = Annotated[int, Field(strict=True, ge=1, le=MAX_LINE_QUANTITY)]
MoneyMinor = Annotated[int, Field(strict=True, ge=0, le=MAX_INT64)]


class OrderStatus(StrEnum):
    """Statuses recognized by the order lifecycle contract."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderLineCreate(BaseModel):
    """Client-supplied item reference and quantity; prices are server-derived."""

    model_config = ConfigDict(extra="forbid")
    inventory_item_id: PositiveId
    quantity: Quantity


class OrderCreate(BaseModel):
    """Checkout input contains 1-100 lines and no client-controlled totals.

    Repeated inventory items are merged into the first occurrence, preserving
    request order. A merged quantity above MAX_LINE_QUANTITY is rejected rather
    than silently truncated.
    """

    model_config = ConfigDict(extra="forbid")
    items: list[OrderLineCreate] = Field(min_length=1, max_length=100)

    @field_validator("items", mode="after")
    @classmethod
    def merge_duplicate_lines(
        cls, lines: list[OrderLineCreate]
    ) -> list[OrderLineCreate]:
        """Field-level so a rejected total is reported at loc ("items",)."""
        merged: dict[int, int] = {}
        for line in lines:
            merged[line.inventory_item_id] = (
                merged.get(line.inventory_item_id, 0) + line.quantity
            )

        for item_id, total in merged.items():
            if total > MAX_LINE_QUANTITY:
                raise ValueError(
                    f"Combined quantity for inventory_item_id {item_id} exceeds "
                    f"{MAX_LINE_QUANTITY}."
                )

        return [
            OrderLineCreate(inventory_item_id=item_id, quantity=total)
            for item_id, total in merged.items()
        ]


class OrderStatusUpdate(BaseModel):
    """Admin status request; allowed transitions are enforced by the service."""

    model_config = ConfigDict(extra="forbid")
    status: OrderStatus


class OrderItemRead(BaseModel):
    """Immutable purchase-time snapshot for one order line."""

    model_config = ConfigDict(extra="forbid", frozen=True, from_attributes=True)
    id: PositiveId
    inventory_item_id: PositiveId
    sku_snapshot: Sku
    name_snapshot: Name
    quantity: Quantity
    unit_price_minor: MoneyMinor
    line_total_minor: MoneyMinor


class OrderRead(BaseModel):
    """Public order view; nested lines can be read from ORM attributes."""

    model_config = ConfigDict(extra="forbid", frozen=True, from_attributes=True)
    id: PositiveId
    user_id: PositiveId
    status: OrderStatus
    currency: Literal["INR"]
    total_minor: MoneyMinor
    version: Annotated[int, Field(strict=True, ge=1, le=MAX_INT64)]
    items: list[OrderItemRead] = Field(min_length=1, max_length=100)
    created_at: datetime
    updated_at: datetime
