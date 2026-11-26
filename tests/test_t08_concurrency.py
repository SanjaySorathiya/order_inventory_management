"""T08 isolated async/sync execution and concurrent-probe tests."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from exercises.t08_concurrency import app as exercise_app
from exercises.t08_concurrency import run_concurrency_probe


@pytest.fixture
def client():
    with TestClient(exercise_app) as test_client:
        yield test_client


def test_async_sleep_uses_event_loop(client) -> None:
    response = client.get("/t08/async-sleep", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["handler"] == "async def"
    assert body["execution"] == "event loop with asyncio.sleep"
    assert isinstance(body["loop_id"], int)


def test_sync_sleep_uses_worker_thread(client) -> None:
    response = client.get("/t08/sync-sleep", params={"seconds": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["handler"] == "def"
    assert body["execution"] == "AnyIO worker thread"
    assert body["thread_name"].startswith("AnyIO worker thread")


def test_async_inline_blocking_runs_synchronous_helper_inline(client) -> None:
    response = client.get(
        "/t08/async-inline-blocking",
        params={"seconds": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["handler"] == "async def"
    assert body["execution"].endswith("synchronous helper ran inline")


@pytest.mark.parametrize("request_count", [1, 0])
def test_concurrency_probe_validates_request_count(request_count) -> None:
    if request_count == 0:
        with pytest.raises(ValueError, match="request_count"):
            asyncio.run(run_concurrency_probe(request_count=request_count))
    else:
        result = asyncio.run(
            run_concurrency_probe(request_count=request_count, delay_seconds=0)
        )
        assert result["slow"]["status_codes"] == [200]
        assert result["health"]["status_codes"] == [200]


def test_concurrent_probe_measures_slow_and_health_routes() -> None:
    result = asyncio.run(run_concurrency_probe(request_count=4, delay_seconds=0.01))

    assert result["request_count"] == 4
    assert result["slow"]["status_codes"] == [200]
    assert result["health"]["status_codes"] == [200]
    assert result["slow"]["average_ms"] >= 0
    assert result["health"]["average_ms"] >= 0


def test_t08_routes_are_absent_from_capstone_openapi() -> None:
    spec = create_app(Settings(_env_file=None, environment="test")).openapi()

    assert {path for path in spec["paths"] if path.startswith("/t08")} == set()
