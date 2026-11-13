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

    model_config = ConfigDict(extra="forbid")
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

    sku: Sku
    description: Description | None = None
    is_active: Annotated[bool, Field(strict=True)] = True


class InventoryPatch(BaseModel):
    """Omission preserves state; only description can explicitly be null."""

    model_config = ConfigDict(extra="forbid")
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

    model_config = ConfigDict(extra="forbid", frozen=True, from_attributes=True)
    id: PositiveId
    sku: Sku
    currency: Literal["INR"] = "INR"
    created_at: datetime
    updated_at: datetime


class InventoryPage(BaseModel):
    """Count is measured after filtering and before pagination."""

    model_config = ConfigDict(extra="forbid")
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
