"""T04 HTTP response contracts for the main API."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

INVENTORY = "/api/v1/inventory"
ITEM = {
    "sku": "HTTP-001",
    "name": "Contract example",
    "unit_price_minor": 12500,
    "stock": 5,
}


@pytest.fixture
def client():
    settings = Settings(_env_file=None, environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_creation_location_resolves_and_deletion_has_no_body(client):
    created = client.post(INVENTORY, json=ITEM)
    assert created.status_code == 201
    location = created.headers["location"]
    assert location == f"{INVENTORY}/{created.json()['id']}"
    fetched = client.get(location)
    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    deleted = client.delete(location)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert "content-type" not in deleted.headers


def test_missing_inventory_has_documented_error_detail(client):
    response = client.get(f"{INVENTORY}/999")
    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "inventory_item_not_found",
            "message": "Inventory item was not found.",
        }
    }


def test_duplicate_inventory_has_documented_conflict_detail(client):
    assert client.post(INVENTORY, json=ITEM).status_code == 201
    response = client.post(INVENTORY, json=ITEM)
    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "code": "duplicate_sku",
            "message": "An inventory item already uses this SKU.",
        }
    }


def test_unsupported_method_preserves_allow_header(client):
    response = client.post("/health")
    assert response.status_code == 405
    allowed = {method.strip() for method in response.headers["allow"].split(",")}
    assert "GET" in allowed
    assert "POST" not in allowed


def test_openapi_creation_and_empty_response_contracts(client):
    paths = client.get("/openapi.json").json()["paths"]
    creation = paths[INVENTORY]["post"]["responses"]
    assert "201" in creation
    assert "200" not in creation
    deletion = paths[f"{INVENTORY}/{{item_id}}"]["delete"]["responses"]
    assert "204" in deletion
    assert "content" not in deletion["204"]


def test_request_exercises_are_absent_from_main_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/headers-cookies",
        "/json",
        "/form",
        "/upload",
        "/errors/rate-limited",
    }.isdisjoint(paths)
