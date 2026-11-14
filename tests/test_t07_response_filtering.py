"""T07 response filtering, nested serialization, and client-versus-server failures."""

import pytest
from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas.auth import UserRead
from app.schemas.orders import OrderItemRead, OrderRead
from exercises.t07_response_filtering import app as exercise_app

PRIVATE_USER_FIELDS = ("password_hash", "is_active", "support_note")
PRIVATE_ORDER_FIELDS = ("cost_minor", "fraud_score")


@pytest.fixture
def client():
    with TestClient(exercise_app) as test_client:
        yield test_client


@pytest.fixture
def client_without_server_exceptions():
    """Let the 500 response reach the test instead of re-raising the server error."""
    with TestClient(exercise_app, raise_server_exceptions=False) as test_client:
        yield test_client


# --- Filtering: only declared public fields leave the server -----------------


def test_user_response_keeps_only_public_fields(client) -> None:
    response = client.get("/t07/users/1")

    assert response.status_code == 200
    assert set(response.json()) == set(UserRead.model_fields)
    for private in PRIVATE_USER_FIELDS:
        assert private not in response.json()
    assert "scrypt" not in response.text


def test_nested_order_is_filtered_at_every_level(client) -> None:
    response = client.get("/t07/orders/42")
    body = response.json()

    assert response.status_code == 200
    assert set(body) == set(OrderRead.model_fields)
    assert len(body["items"]) == 2
    for line in body["items"]:
        assert set(line) == set(OrderItemRead.model_fields)
    for private in PRIVATE_ORDER_FIELDS:
        assert private not in response.text


def test_nested_serialization_preserves_public_values(client) -> None:
    body = client.get("/t07/orders/42").json()

    assert body["total_minor"] == 37500
    assert [line["line_total_minor"] for line in body["items"]] == [25000, 12500]
    assert body["items"][0]["sku_snapshot"] == "KB-001"
    assert body["created_at"] == "2026-11-14T10:00:00Z"


# --- Client invalid input versus server invalid response --------------------


def test_invalid_client_body_is_422_and_leaves_server_healthy(client) -> None:
    response = client.post(
        "/t07/users/validate",
        json={"username": "ab", "password": "x", "grant_type": "password"},
    )

    assert response.status_code == 422
    locations = [error["loc"] for error in response.json()["detail"]]
    assert ["body", "username"] in locations
    assert "ab" not in response.text

    valid = client.post(
        "/t07/users/validate",
        json={"username": "customer.one", "password": "x", "grant_type": "password"},
    )
    assert valid.status_code == 200
    assert valid.json() == {"id": 1, "username": "customer.one", "role": "customer"}


def test_server_response_with_private_key_is_500_not_422(
    client_without_server_exceptions,
) -> None:
    response = client_without_server_exceptions.get("/t07/users-leaky")

    assert response.status_code == 500
    assert "scrypt" not in response.text
    assert "password_hash" not in response.text


def test_server_response_error_is_raised_to_direct_callers(client) -> None:
    """Without the ASGI error boundary, a bad server response surfaces as an exception."""
    with pytest.raises(ResponseValidationError):
        client.get("/t07/users-leaky")
    with pytest.raises(ResponseValidationError):
        client.get("/t07/users-incomplete")


def test_server_response_missing_required_field_is_500(
    client_without_server_exceptions,
) -> None:
    response = client_without_server_exceptions.get("/t07/users-incomplete")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/plain")


# --- Isolation from the capstone API ----------------------------------------


def test_exercise_routes_are_absent_from_capstone_openapi() -> None:
    capstone = create_app(Settings(_env_file=None, environment="test"))
    paths = capstone.openapi()["paths"]

    assert {p for p in paths if p.startswith("/t07")} == set()


def test_exercise_app_is_a_fastapi_instance() -> None:
    assert isinstance(exercise_app, FastAPI)
