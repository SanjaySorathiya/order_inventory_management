"""Isolated T07 response filtering and invalid-response demonstrations.

Run separately from the capstone API. Internal records below hold a password
hash and private flags; the public response models decide what leaves the server.
The `/t07/users-leaky` and `/t07/users-incomplete` routes are intentionally broken.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import validation_error_response
from app.schemas.auth import LoginInput, UserRead
from app.schemas.orders import OrderRead

app = FastAPI(
    title="T07 response filtering exercises",
    description=(
        "Isolated learning examples. Internal records are never returned directly; "
        "public response models filter them. Two routes are intentionally broken."
    ),
)
app.add_exception_handler(RequestValidationError, validation_error_response)

_NOW = datetime(2026, 11, 14, 10, 0, tzinfo=UTC)


@dataclass
class InternalUser:
    """Storage shape: includes credentials and account flags that are never public."""

    id: int
    username: str
    role: Literal["customer", "admin"]
    password_hash: str
    is_active: bool
    support_note: str


@dataclass
class InternalOrderLine:
    """Purchase-time line with a private cost used for margin reporting only."""

    id: int
    inventory_item_id: int
    sku_snapshot: str
    name_snapshot: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int
    cost_minor: int


@dataclass
class InternalOrder:
    """Order storage shape with a private fraud score beside the public fields."""

    id: int
    user_id: int
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    currency: Literal["INR"]
    total_minor: int
    version: int
    items: list[InternalOrderLine]
    created_at: datetime
    updated_at: datetime
    fraud_score: int


USERS = {
    1: InternalUser(
        id=1,
        username="admin",
        role="admin",
        password_hash="scrypt$demo-salt$demo-digest",
        is_active=True,
        support_note="Escalate chargeback disputes to finance.",
    )
}

ORDERS = {
    42: InternalOrder(
        id=42,
        user_id=7,
        status="pending",
        currency="INR",
        total_minor=37500,
        version=1,
        items=[
            InternalOrderLine(
                id=1,
                inventory_item_id=1,
                sku_snapshot="KB-001",
                name_snapshot="Keyboard",
                quantity=2,
                unit_price_minor=12500,
                line_total_minor=25000,
                cost_minor=7000,
            ),
            InternalOrderLine(
                id=2,
                inventory_item_id=2,
                sku_snapshot="MS-002",
                name_snapshot="Mouse",
                quantity=1,
                unit_price_minor=12500,
                line_total_minor=12500,
                cost_minor=4000,
            ),
        ],
        created_at=_NOW,
        updated_at=_NOW,
        fraud_score=12,
    )
}


@app.get(
    "/t07/users/{user_id}",
    response_model=UserRead,
    summary="Public user (filtered)",
    description="Returns an InternalUser through UserRead; credentials and flags are dropped.",
)
def read_user(user_id: int) -> InternalUser:
    return USERS[user_id]


@app.get(
    "/t07/orders/{order_id}",
    response_model=OrderRead,
    summary="Public order with nested lines (filtered)",
    description="Returns an InternalOrder through OrderRead; nested cost and fraud fields are dropped.",
)
def read_order(order_id: int) -> InternalOrder:
    return ORDERS[order_id]


@app.post(
    "/t07/users/validate",
    response_model=UserRead,
    summary="Validate login input (client errors)",
    description=(
        "Invalid request bodies return 422 from input validation. A valid body "
        "returns a public user, so client and server failures can be compared."
    ),
)
def validate_login(body: LoginInput) -> UserRead:
    return UserRead(id=1, username=body.username, role="customer")


@app.get(
    "/t07/users-leaky",
    response_model=UserRead,
    summary="Intentionally broken: dict with a private key (server error)",
    description=(
        "Returns a dict containing password_hash. UserRead forbids extra keys, so "
        "FastAPI raises ResponseValidationError and the client receives a 500."
    ),
)
def users_leaky() -> dict[str, object]:
    user = USERS[1]
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "password_hash": user.password_hash,
    }


@app.get(
    "/t07/users-incomplete",
    response_model=UserRead,
    summary="Intentionally broken: dict missing a required field (server error)",
    description="Omits username, so the server response is invalid and returns a 500.",
)
def users_incomplete() -> dict[str, object]:
    return {"id": 1, "role": "admin"}
