"""Behavioral coverage for the temporary in-memory inventory API."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

BASE = "/api/v1/inventory"
MAX_INT64 = 2**63 - 1
CREATE = {
    "sku": "KB-001",
    "name": "Keyboard",
    "description": "Original description",
    "unit_price_minor": 12500,
    "stock": 5,
}
REPLACE = {
    "name": "Replacement keyboard",
    "description": None,
    "unit_price_minor": 15000,
    "stock": 8,
    "is_active": True,
}


@pytest.fixture
def client():
    settings = Settings(_env_file=None, environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def create_item(client, **changes):
    response = client.post(BASE, json={**CREATE, **changes})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def catalog(client):
    rows = [
        ("LITERAL-1", "USB%_ Cable", 100, 0),
        ("USB-2", "USB Cable", 100, 3),
        ("MOUSE-1", "Mouse", 500, 2),
        ("MOUSE-2", "Mouse", 500, 0),
    ]
    items = [
        create_item(client, sku=sku, name=name, unit_price_minor=price, stock=stock)
        for sku, name, price, stock in rows
    ]
    create_item(client, sku="HIDDEN", name="Hidden mouse", is_active=False)
    return [item["id"] for item in items]


def test_create_and_read_normalized_item(client):
    response = client.post(
        BASE, json={**CREATE, "sku": " kb-001 ", "name": " Keyboard "}
    )
    assert response.status_code == 201
    item = response.json()
    assert response.headers["location"] == f"{BASE}/{item['id']}"
    assert item["sku"] == "KB-001"
    assert item["name"] == "Keyboard"
    assert item["currency"] == "INR"
    assert item["is_active"] is True
    assert item["created_at"].endswith("Z")
    assert item["updated_at"].endswith("Z")
    assert client.get(f"{BASE}/{item['id']}").json() == item


def test_create_defaults_and_empty_list(client):
    assert client.get(BASE).json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    body = {key: value for key, value in CREATE.items() if key != "description"}
    response = client.post(BASE, json=body)
    assert response.status_code == 201
    assert response.json()["description"] is None
    assert response.json()["is_active"] is True


def test_put_replaces_all_mutable_fields_and_preserves_identity(client):
    original = create_item(client)
    response = client.put(f"{BASE}/{original['id']}", json=REPLACE)
    assert response.status_code == 200
    updated = response.json()
    for key, value in REPLACE.items():
        assert updated[key] == value
    for key in ("id", "sku", "currency", "created_at"):
        assert updated[key] == original[key]
    assert client.get(f"{BASE}/{original['id']}").json() == updated


@pytest.mark.parametrize("missing", list(REPLACE))
def test_put_requires_every_mutable_field(client, missing):
    original = create_item(client)
    body = {key: value for key, value in REPLACE.items() if key != missing}
    response = client.put(f"{BASE}/{original['id']}", json=body)
    assert response.status_code == 422
    assert client.get(f"{BASE}/{original['id']}").json() == original


def test_patch_preserves_omitted_fields_and_can_clear_description(client):
    original = create_item(client)
    path = f"{BASE}/{original['id']}"
    response = client.patch(path, json={"stock": 2})
    assert response.status_code == 200
    updated = response.json()
    assert updated["stock"] == 2
    for key in ("sku", "name", "description", "unit_price_minor", "is_active"):
        assert updated[key] == original[key]
    response = client.patch(path, json={"description": None})
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["stock"] == 2


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": None},
        {"unit_price_minor": None},
        {"stock": None},
        {"is_active": None},
        {"sku": "NEW-SKU"},
        {"id": 10},
        {"currency": "USD"},
        {"unknown": "value"},
    ],
)
def test_patch_rejects_invalid_or_immutable_fields_without_mutation(client, body):
    original = create_item(client)
    path = f"{BASE}/{original['id']}"
    assert client.patch(path, json=body).status_code == 422
    assert client.get(path).json() == original


def test_delete_deactivates_idempotently_and_patch_can_reactivate(client):
    original = create_item(client)
    path = f"{BASE}/{original['id']}"
    for _ in range(2):
        response = client.delete(path)
        assert response.status_code == 204
        assert response.content == b""
    assert client.get(path).status_code == 404
    assert client.get(BASE).json()["items"] == []
    response = client.patch(path, json={"is_active": True})
    assert response.status_code == 200
    assert response.json()["id"] == original["id"]
    assert response.json()["stock"] == original["stock"]
    assert client.get(path).status_code == 200


def test_put_can_reactivate_an_inactive_item(client):
    item = create_item(client, is_active=False)
    path = f"{BASE}/{item['id']}"
    assert client.get(path).status_code == 404
    assert client.put(path, json=REPLACE).status_code == 200
    assert client.get(path).json()["is_active"] is True


def test_normalized_sku_is_unique_even_after_deactivation(client):
    item = create_item(client)
    client.delete(f"{BASE}/{item['id']}")
    response = client.post(BASE, json={**CREATE, "sku": " kb-001 "})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicate_sku"
    assert client.get(BASE).json()["total"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stock", True),
        ("stock", "1"),
        ("stock", 1.5),
        ("stock", None),
        ("stock", -1),
        ("stock", MAX_INT64 + 1),
        ("unit_price_minor", False),
        ("unit_price_minor", "100"),
        ("unit_price_minor", 1.5),
        ("unit_price_minor", None),
        ("unit_price_minor", -1),
        ("unit_price_minor", MAX_INT64 + 1),
        ("name", " "),
        ("name", "x" * 121),
        ("sku", "bad sku"),
        ("sku", "x" * 65),
        ("description", "x" * 1001),
        ("is_active", "true"),
        ("unknown", "value"),
    ],
)
def test_create_rejects_invalid_body_without_creating_item(client, field, value):
    response = client.post(BASE, json={**CREATE, field: value})
    assert response.status_code == 422
    assert client.get(BASE).json()["total"] == 0


@pytest.mark.parametrize("item_id", ["0", "-1", "abc", "1.5"])
@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_resource_identifiers_are_validated(client, item_id, method):
    kwargs = {}
    if method == "put":
        kwargs["json"] = REPLACE
    elif method == "patch":
        kwargs["json"] = {"stock": 1}
    response = client.request(method, f"{BASE}/{item_id}", **kwargs)
    assert response.status_code == 422
    assert any(error["loc"][0] == "path" for error in response.json()["detail"])


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_missing_resource_returns_404_without_upsert(client, method):
    kwargs = {}
    if method == "put":
        kwargs["json"] = REPLACE
    elif method == "patch":
        kwargs["json"] = {"stock": 1}
    response = client.request(method, f"{BASE}/999", **kwargs)
    assert response.status_code == 404
    assert client.get(BASE).json()["total"] == 0


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "0"},
        {"limit": "101"},
        {"limit": "1.5"},
        {"offset": "-1"},
        {"offset": "abc"},
        {"sort": "stock"},
        {"direction": "up"},
        {"q": ""},
        {"q": "   "},
        {"q": "x" * 121},
        {"in_stock": "1"},
        {"in_stock": "yes"},
        {"in_stock": "True"},
        {"in_stock": ""},
        {"include_inactive": "FALSE"},
        {"unexpected": "value"},
        [("limit", "1"), ("limit", "2")],
        [("q", "mouse"), ("q", "cable")],
        [("in_stock", "true"), ("in_stock", "false")],
    ],
)
def test_inventory_rejects_invalid_unknown_and_repeated_queries(client, params):
    response = client.get(BASE, params=params)
    assert response.status_code == 422
    assert any(error["loc"][0] == "query" for error in response.json()["detail"])


def test_query_filters_are_literal_trimmed_and_case_insensitive(client, catalog):
    response = client.get(BASE, params={"q": "  mOuSe  ", "in_stock": "true"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [catalog[2]]
    response = client.get(BASE, params={"q": "%_"})
    assert [item["id"] for item in response.json()["items"]] == [catalog[0]]
    response = client.get(BASE, params={"q": "usb-2"})
    assert [item["id"] for item in response.json()["items"]] == [catalog[1]]
    response = client.get(BASE, params={"q": "absent"})
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_stock_filter_distinguishes_omitted_true_and_false(client, catalog):
    assert client.get(BASE).json()["total"] == 4
    positive = client.get(BASE, params={"in_stock": "true"}).json()
    zero = client.get(BASE, params={"in_stock": "false"}).json()
    assert [item["id"] for item in positive["items"]] == [catalog[1], catalog[2]]
    assert [item["id"] for item in zero["items"]] == [catalog[0], catalog[3]]


@pytest.mark.parametrize(
    ("sort", "direction", "positions"),
    [
        ("id", "desc", [3, 2, 1, 0]),
        ("name", "asc", [2, 3, 1, 0]),
        ("name", "desc", [0, 1, 2, 3]),
        ("unit_price_minor", "desc", [2, 3, 0, 1]),
    ],
)
def test_sorting_keeps_id_ascending_as_final_tiebreaker(
    client, catalog, sort, direction, positions
):
    response = client.get(BASE, params={"sort": sort, "direction": direction})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [
        catalog[position] for position in positions
    ]


def test_pagination_uses_filtered_total_before_slicing(client, catalog):
    response = client.get(BASE, params={"in_stock": "true", "limit": 1, "offset": 1})
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 2
    assert page["limit"] == 1
    assert page["offset"] == 1
    assert [item["id"] for item in page["items"]] == [catalog[2]]
    page = client.get(BASE, params={"limit": 100, "offset": 100}).json()
    assert page["items"] == []
    assert page["total"] == 4


def test_anonymous_caller_cannot_include_inactive_inventory(client, catalog):
    response = client.get(BASE, params={"include_inactive": "true"})
    assert response.status_code == 403
    assert client.get(BASE, params={"include_inactive": "false"}).json()["total"] == 4


def test_factory_instances_do_not_share_inventory(client):
    create_item(client)
    settings = Settings(_env_file=None, environment="test")
    with TestClient(create_app(settings)) as other_client:
        assert other_client.get(BASE).json()["total"] == 0
    assert client.get(BASE).json()["total"] == 1


def test_production_inventory_writes_are_disabled():
    settings = Settings(_env_file=None, environment="production")
    with TestClient(create_app(settings)) as client:
        for method, path, body in [
            ("post", BASE, CREATE),
            ("put", f"{BASE}/1", REPLACE),
            ("patch", f"{BASE}/1", {"stock": 2}),
            ("delete", f"{BASE}/1", None),
        ]:
            response = client.request(method, path, json=body)
            assert response.status_code == 501
            assert (
                response.json()["detail"]["code"]
                == "inventory_administration_not_ready"
            )
        assert client.get(BASE).json()["total"] == 0


@pytest.mark.parametrize(
    ("method", "body"),
    [
        ("post", {**CREATE, "password": "private-request-value"}),
        ("post", {**CREATE, "access_token": "private-request-value"}),
        ("patch", {"name": None, "description": "private-request-value"}),
    ],
)
def test_validation_errors_do_not_echo_submitted_secrets(client, method, body):
    path = BASE if method == "post" else f"{BASE}/1"
    response = client.request(method, path, json=body)
    assert response.status_code == 422
    assert "private-request-value" not in response.text
    assert all(
        {"loc", "msg", "type"} == error.keys() for error in response.json()["detail"]
    )
