"""Tests for the T05 domain request/output schemas and static verifier."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginInput, UserRead
from app.schemas.orders import (
    OrderCreate,
    OrderLineCreate,
    OrderStatus,
    OrderStatusUpdate,
)
from app.services.auth import StaticCredentialVerifier


def test_order_create_accepts_integer_quantities_and_nested_fields() -> None:
    order = OrderCreate.model_validate(
        {"items": [{"inventory_item_id": 12, "quantity": 3}]}
    )

    assert order.items == [OrderLineCreate(inventory_item_id=12, quantity=3)]


@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": [{"inventory_item_id": 12, "quantity": "3"}]},
        {"items": [{"inventory_item_id": 12, "quantity": True}]},
        {"items": [{"inventory_item_id": 12, "quantity": 3, "unit_price_minor": 1}]},
        {"items": [{"inventory_item_id": 0, "quantity": 3}]},
    ],
)
def test_order_create_rejects_invalid_or_extra_input(payload: object) -> None:
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(payload)


def test_order_status_update_uses_contract_status_vocabulary() -> None:
    assert OrderStatusUpdate(status="processing").status is OrderStatus.PROCESSING
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="unknown")


def test_login_normalizes_username_but_preserves_password() -> None:
    login = LoginInput(username=" ADMIN ", password=" password ", grant_type="password")

    assert login.username == "admin"
    assert login.password == " password "
    assert login.scope == ""


def test_static_credential_verifier_returns_public_user_only() -> None:
    verifier = StaticCredentialVerifier()
    credentials = LoginInput(
        username="admin", password="password", grant_type="password"
    )

    user = verifier.authenticate(credentials)

    assert user == UserRead(id=1, username="admin", role="admin")
    assert user.model_dump() == {"id": 1, "username": "admin", "role": "admin"}
    assert (
        verifier.authenticate(credentials.model_copy(update={"password": "incorrect"}))
        is None
    )
