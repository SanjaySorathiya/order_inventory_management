"""Behavioral checks for the isolated T03 parameter exercises."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exercises.t03_parameters import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("missing", ["required", "required_nullable"])
def test_nullable_without_default_is_still_required(client, missing):
    params = {
        key: "value" for key in ("required", "required_nullable") if key != missing
    }
    response = client.get("/parameters", params=params)
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", missing] and error["type"] == "missing"
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    ("optional_query", "expected"),
    [
        ({}, None),
        ({"optional_nullable": ""}, ""),
        ({"optional_nullable": "provided"}, "provided"),
        ({"optional_nullable": "null"}, "null"),
    ],
)
def test_optional_omission_empty_value_and_literal_null(
    client, optional_query, expected
):
    response = client.get(
        "/parameters",
        params={
            "required": "value",
            "required_nullable": "null",
            **optional_query,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "required": "value",
        "required_nullable": "null",
        "optional_nullable": expected,
    }


def test_openapi_distinguishes_required_nullable_from_optional(client):
    operation = client.get("/openapi.json").json()["paths"]["/parameters"]["get"]
    parameters = {value["name"]: value for value in operation["parameters"]}
    assert parameters["required"]["required"] is True
    assert parameters["required_nullable"]["required"] is True
    assert parameters["optional_nullable"]["required"] is False
    assert {
        option["type"] for option in parameters["required_nullable"]["schema"]["anyOf"]
    } == {"string", "null"}


def test_static_route_precedes_dynamic_route(client):
    response = client.get("/items/search")
    assert response.status_code == 200
    assert response.json() == {"route": "search"}
    response = client.get("/items/7")
    assert response.status_code == 200
    assert response.json() == {"item_id": 7}


@pytest.mark.parametrize("item_id", ["0", "-1", "abc", "1.5"])
def test_dynamic_route_rejects_invalid_identifiers(client, item_id):
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 422
    assert any(
        error["loc"] == ["path", "item_id"] for error in response.json()["detail"]
    )


def test_dynamic_first_shadows_a_later_static_route():
    misordered = FastAPI()

    @misordered.get("/items/{item_id}")
    async def dynamic_first(item_id: int):
        return {"item_id": item_id}

    @misordered.get("/items/search")
    async def static_second():
        return {"route": "search"}

    with TestClient(misordered) as client:
        response = client.get("/items/search")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "item_id"]
