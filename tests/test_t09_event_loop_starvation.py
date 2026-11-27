"""T09 event-loop starvation exercise tests."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from exercises.t09_event_loop_starvation import app as exercise_app
from exercises.t09_event_loop_starvation import (
    run_starvation_probe,
)


@pytest.fixture
def client():
    with TestClient(exercise_app) as test_client:
        yield test_client


def test_blocking_inline_runs_on_event_loop(client) -> None:
    response = client.get("/t09/blocking-inline", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["handler"] == "async def"
    assert body["execution"].startswith("blocking call ran inline")


def test_async_native_uses_async_sleep(client) -> None:
    response = client.get("/t09/async-native", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["execution"] == "async-native asyncio.sleep"


def test_to_thread_offloads_blocking_helper(client) -> None:
    response = client.get("/t09/to-thread", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["execution"].endswith("asyncio.to_thread")
    assert body["thread_name"] != "MainThread"


def test_sync_route_uses_worker_thread(client) -> None:
    response = client.get("/t09/sync", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["handler"] == "def"
    assert body["thread_name"].startswith("AnyIO worker thread")


@pytest.mark.parametrize("request_count", [1, 0])
def test_starvation_probe_validates_request_count(request_count) -> None:
    if request_count == 0:
        with pytest.raises(ValueError, match="request_count"):
            asyncio.run(run_starvation_probe(request_count=request_count))
    else:
        result = asyncio.run(
            run_starvation_probe(
                request_count=request_count,
                delay_seconds=0,
            )
        )
        assert result["blocking_route"]["status_codes"] == [200]
        assert result["health"]["status_codes"] == [200]


@pytest.mark.parametrize(
    "route",
    [
        "/t09/blocking-inline",
        "/t09/async-native",
        "/t09/to-thread",
        "/t09/sync",
    ],
)
def test_starvation_probe_covers_all_variants(route) -> None:
    result = asyncio.run(
        run_starvation_probe(
            route=route,
            request_count=4,
            delay_seconds=0.01,
        )
    )

    assert result["route"] == route
    assert result["blocking_route"]["status_codes"] == [200]
    assert result["health"]["status_codes"] == [200]


def test_unknown_probe_route_is_rejected() -> None:
    with pytest.raises(ValueError, match="route must be"):
        asyncio.run(run_starvation_probe(route="/t09/unknown"))


def test_t09_routes_are_absent_from_capstone_openapi() -> None:
    spec = create_app(Settings(_env_file=None, environment="test")).openapi()

    assert {path for path in spec["paths"] if path.startswith("/t09")} == set()
