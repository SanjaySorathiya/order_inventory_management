"""Domain request and response schemas needed by T03 and T05."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

MAX_INT64 = 2**63 - 1
Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]
Sku = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$",
    ),
]
Description = Annotated[str, Field(max_length=1000)]
NonnegativeInt = Annotated[int, Field(strict=True, ge=0, le=MAX_INT64)]
PositiveId = Annotated[int, Field(strict=True, gt=0, le=MAX_INT64)]


def collapse_inner_whitespace(value: str) -> str:
    """Collapse internal whitespace runs after Name has stripped the ends."""
    return " ".join(value.split())


class InventoryReplace(BaseModel):
    """PUT supplies every mutable field, including nullable description."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Keyboard",
                    "description": "Compact layout",
                    "unit_price_minor": 12500,
                    "stock": 3,
                    "is_active": True,
                }
            ]
        },
    )
    name: Name
    description: Description | None
    unit_price_minor: NonnegativeInt
    stock: NonnegativeInt
    is_active: Annotated[bool, Field(strict=True)]

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return collapse_inner_whitespace(value)


class InventoryCreate(InventoryReplace):
    """Creation adds an immutable SKU and defaults for optional fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sku": "KB-001",
                    "name": "Keyboard",
                    "description": None,
                    "unit_price_minor": 12500,
                    "stock": 5,
                    "is_active": True,
                }
            ]
        },
    )
    sku: Sku
    description: Description | None = None
    is_active: Annotated[bool, Field(strict=True)] = True


class InventoryPatch(BaseModel):
    """Omission preserves state; only description can explicitly be null."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"stock": 3}, {"description": None}]},
    )
    name: Name | None = None
    description: Description | None = None
    unit_price_minor: NonnegativeInt | None = None
    stock: NonnegativeInt | None = None
    is_active: Annotated[bool, Field(strict=True)] | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return collapse_inner_whitespace(value)

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("PATCH must contain at least one mutable field.")
        for field in self.model_fields_set - {"description"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        return self


class InventoryRead(InventoryReplace):
    """Public inventory representation compatible with ORM attributes."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "sku": "KB-001",
                    "name": "Keyboard",
                    "description": "Compact layout",
                    "unit_price_minor": 12500,
                    "stock": 3,
                    "is_active": True,
                    "currency": "INR",
                    "created_at": "2026-11-14T10:00:00Z",
                    "updated_at": "2026-11-14T10:00:00Z",
                }
            ]
        },
    )
    id: PositiveId
    sku: Sku
    currency: Literal["INR"] = "INR"
    created_at: datetime
    updated_at: datetime


class InventoryPage(BaseModel):
    """Count is measured after filtering and before pagination."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": 1,
                            "sku": "KB-001",
                            "name": "Keyboard",
                            "description": "Compact layout",
                            "unit_price_minor": 12500,
                            "stock": 3,
                            "is_active": True,
                            "currency": "INR",
                            "created_at": "2026-11-14T10:00:00Z",
                            "updated_at": "2026-11-14T10:00:00Z",
                        }
                    ],
                    "total": 1,
                    "limit": 20,
                    "offset": 0,
                }
            ]
        },
    )
    items: list[InventoryRead]
    total: int
    limit: int
    offset: int


class InventoryQuery(BaseModel):
    """Query strings use literal true/false rather than permissive bool coercion."""

    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    q: Name | None = None
    in_stock: Literal["true", "false"] | None = None
    sort: Literal["id", "name", "unit_price_minor"] = "id"
    direction: Literal["asc", "desc"] = "asc"
    include_inactive: Literal["true", "false"] = "false"
