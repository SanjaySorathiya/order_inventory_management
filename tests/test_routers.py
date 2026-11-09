"""Versioned route registration and explicit pending workflows."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None, environment="test"))) as client:
        yield client


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/v1/auth/token"),
        ("post", "/api/v1/orders"),
        ("get", "/api/v1/orders/1"),
        ("patch", "/api/v1/orders/1/status"),
        ("get", "/api/v1/orders/1/events"),
    ],
)
def test_future_workflows_explicitly_return_501(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 501
    assert "not_implemented" in response.json()["detail"]["code"]


@pytest.mark.parametrize("order_id", ["0", "-1", "abc", "1.5"])
@pytest.mark.parametrize("suffix", ["", "/status", "/events"])
def test_order_placeholder_still_validates_path(client, order_id, suffix):
    method = "patch" if suffix == "/status" else "get"
    response = client.request(method, f"/api/v1/orders/{order_id}{suffix}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "order_id"]


def test_openapi_registers_versioned_routes_with_tags_and_query_bounds(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert paths["/api/v1/auth/token"]["post"]["tags"] == ["Auth"]
    assert paths["/api/v1/orders/{order_id}"]["get"]["tags"] == ["Orders"]
    catalog = paths["/api/v1/inventory"]
    assert {"get", "post"} <= catalog.keys()
    detail = paths["/api/v1/inventory/{item_id}"]
    assert {"get", "put", "patch", "delete"} <= detail.keys()
    assert catalog["get"]["tags"] == ["Inventory"]
    assert paths["/health"]["get"]["tags"] == ["Health"]
    parameters = {p["name"]: p for p in catalog["get"]["parameters"]}
    assert parameters["limit"]["schema"]["minimum"] == 1
    assert parameters["limit"]["schema"]["maximum"] == 100
    assert parameters["offset"]["schema"]["minimum"] == 0
    assert parameters["limit"]["required"] is False
    assert "securitySchemes" not in schema.get("components", {})
