"""T06 validators, PATCH dump semantics, and structured 422 responses."""

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.errors import validation_error_response
from app.core.config import Settings
from app.main import create_app
from app.schemas.inventory import InventoryCreate, InventoryPatch
from app.schemas.orders import MAX_LINE_QUANTITY, OrderCreate, OrderLineCreate

INVENTORY = "/api/v1/inventory"


# --- Order validators: duplicate merge, cap, and empty orders ----------------


def test_duplicate_lines_merge_into_first_occurrence_in_request_order() -> None:
    order = OrderCreate.model_validate(
        {
            "items": [
                {"inventory_item_id": 3, "quantity": 2},
                {"inventory_item_id": 1, "quantity": 1},
                {"inventory_item_id": 3, "quantity": 5},
            ]
        }
    )

    assert order.items == [
        OrderLineCreate(inventory_item_id=3, quantity=7),
        OrderLineCreate(inventory_item_id=1, quantity=1),
    ]


def test_merged_quantity_at_the_cap_is_accepted() -> None:
    order = OrderCreate.model_validate(
        {
            "items": [
                {"inventory_item_id": 9, "quantity": MAX_LINE_QUANTITY - 1},
                {"inventory_item_id": 9, "quantity": 1},
            ]
        }
    )

    assert order.items == [
        OrderLineCreate(inventory_item_id=9, quantity=MAX_LINE_QUANTITY)
    ]


def test_merged_quantity_above_the_cap_is_rejected_at_items_field() -> None:
    with pytest.raises(ValidationError) as excinfo:
        OrderCreate.model_validate(
            {
                "items": [
                    {"inventory_item_id": 1, "quantity": 6_000},
                    {"inventory_item_id": 1, "quantity": 6_000},
                ]
            }
        )

    errors = excinfo.value.errors()
    assert [error["loc"] for error in errors] == [("items",)]
    assert "exceeds 10000" in errors[0]["msg"]


def test_empty_order_is_rejected_by_length_constraint() -> None:
    with pytest.raises(ValidationError) as excinfo:
        OrderCreate.model_validate({"items": []})

    assert [error["type"] for error in excinfo.value.errors()] == ["too_short"]


def test_order_with_more_than_100_lines_is_rejected() -> None:
    lines = [{"inventory_item_id": i, "quantity": 1} for i in range(1, 102)]

    with pytest.raises(ValidationError) as excinfo:
        OrderCreate.model_validate({"items": lines})

    assert excinfo.value.errors()[0]["type"] == "too_long"


# --- Strict versus coercible input ------------------------------------------


@pytest.mark.parametrize("quantity", [0, -1, MAX_LINE_QUANTITY + 1])
def test_quantity_outside_bounds_is_rejected(quantity: int) -> None:
    with pytest.raises(ValidationError):
        OrderLineCreate(inventory_item_id=1, quantity=quantity)


@pytest.mark.parametrize("quantity", ["3", 2.0, True, None])
def test_quantity_is_strict_and_never_coerced(quantity: object) -> None:
    with pytest.raises(ValidationError):
        OrderLineCreate.model_validate({"inventory_item_id": 1, "quantity": quantity})


def test_sku_is_normalized_by_annotation_not_by_coercion() -> None:
    item = InventoryCreate(sku="  ab-1 ", name="Widget", unit_price_minor=100, stock=0)

    assert item.sku == "AB-1"


# --- Field normalization: inventory name ------------------------------------


def test_create_name_collapses_inner_whitespace() -> None:
    item = InventoryCreate(
        sku="W-1", name="  Blue \t  Widget \n XL ", unit_price_minor=1, stock=0
    )

    assert item.name == "Blue Widget XL"


def test_whitespace_only_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        InventoryCreate(sku="W-2", name="   \t ", unit_price_minor=1, stock=0)


def test_patch_name_is_normalized_when_supplied() -> None:
    assert InventoryPatch(name="  Blue   Widget ").name == "Blue Widget"


def test_patch_null_name_is_rejected_not_normalized() -> None:
    with pytest.raises(ValidationError):
        InventoryPatch(name=None)


# --- PATCH: exclude_unset and explicit null ---------------------------------


def test_patch_exclude_unset_keeps_only_supplied_fields() -> None:
    patch = InventoryPatch(stock=5)

    assert patch.model_dump(exclude_unset=True) == {"stock": 5}
    assert patch.model_dump() == {
        "name": None,
        "description": None,
        "unit_price_minor": None,
        "stock": 5,
        "is_active": None,
    }


def test_patch_explicit_null_description_is_distinct_from_omission() -> None:
    clear_description = InventoryPatch(description=None)

    assert clear_description.model_dump(exclude_unset=True) == {"description": None}
    assert "description" not in InventoryPatch(stock=1).model_dump(exclude_unset=True)


def test_empty_patch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        InventoryPatch()


# --- Structured 422 responses -----------------------------------------------


@pytest.fixture
def client():
    settings = Settings(_env_file=None, environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def assert_structured_422(response, *expected_locs: tuple) -> list[dict]:
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert set(detail[0]) == {"loc", "msg", "type"}
    assert [tuple(error["loc"]) for error in detail] == list(expected_locs)
    return detail


def test_invalid_inventory_body_returns_locations_and_no_submitted_values(
    client,
) -> None:
    response = client.post(
        INVENTORY,
        json={
            "sku": "T6-001",
            "name": "   ",
            "unit_price_minor": "12500",
            "stock": 5,
            "is_active": True,
        },
    )

    detail = assert_structured_422(
        response,
        ("body", "name"),
        ("body", "unit_price_minor"),
    )
    assert detail[1]["type"] == "int_type"
    assert "12500" not in response.text
    assert "   " not in response.text


def test_empty_patch_returns_422_at_body_location(client) -> None:
    created = client.post(
        INVENTORY,
        json={"sku": "T6-002", "name": "Patch me", "unit_price_minor": 1, "stock": 1},
    )
    item_id = created.json()["id"]

    response = client.patch(f"{INVENTORY}/{item_id}", json={})

    assert_structured_422(response, ("body",))


def test_invalid_path_identifier_returns_path_location(client) -> None:
    response = client.get(f"{INVENTORY}/0")

    assert_structured_422(response, ("path", "item_id"))


def test_order_validation_failures_render_items_location() -> None:
    """Probe route: order routes are still 501, so the schema is exercised here."""
    probe = FastAPI()
    probe.add_exception_handler(RequestValidationError, validation_error_response)

    @probe.post("/probe-order")
    def probe_order(body: OrderCreate) -> dict[str, int]:
        return {"lines": len(body.items)}

    with TestClient(probe) as probe_client:
        ok = probe_client.post(
            "/probe-order",
            json={
                "items": [
                    {"inventory_item_id": 2, "quantity": 1},
                    {"inventory_item_id": 2, "quantity": 4},
                ]
            },
        )
        assert ok.status_code == 200
        assert ok.json() == {"lines": 1}

        over_cap = probe_client.post(
            "/probe-order",
            json={
                "items": [
                    {"inventory_item_id": 2, "quantity": 9_999},
                    {"inventory_item_id": 2, "quantity": 2},
                ]
            },
        )
        assert_structured_422(over_cap, ("body", "items"))

        empty = probe_client.post("/probe-order", json={"items": []})
        assert_structured_422(empty, ("body", "items"))

        extra_field = probe_client.post(
            "/probe-order",
            json={
                "items": [
                    {"inventory_item_id": 2, "quantity": 1, "unit_price_minor": 1}
                ]
            },
        )
        assert_structured_422(extra_field, ("body", "items", 0, "unit_price_minor"))
