"""Order request and response schemas for checkout and status workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inventory import MAX_INT64, Name, PositiveId, Sku

Quantity = Annotated[int, Field(strict=True, ge=1, le=10_000)]
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
    """Checkout input contains 1-100 lines and no client-controlled totals."""

    model_config = ConfigDict(extra="forbid")
    items: list[OrderLineCreate] = Field(min_length=1, max_length=100)


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
