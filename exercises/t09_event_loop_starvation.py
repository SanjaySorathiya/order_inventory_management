"""Isolated T09 event-loop starvation exercises."""

import asyncio
import statistics
import threading
import time
from typing import Any

import httpx
from fastapi import FastAPI, Query

app = FastAPI(
    title="T09 event-loop starvation exercises",
    description=(
        "Isolated blocking-I/O demonstrations. Run separately from the capstone API."
    ),
)


def _blocking_sleep(seconds: float) -> dict[str, object]:
    time.sleep(seconds)
    return {
        "thread_name": threading.current_thread().name,
        "thread_ident": threading.get_ident(),
    }


@app.get("/t09/health", tags=["T09"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/t09/blocking-inline", tags=["T09"])
async def blocking_inline(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    timing = _blocking_sleep(seconds)
    return {
        "handler": "async def",
        "execution": "blocking call ran inline on the event-loop thread",
        **timing,
    }


@app.get("/t09/async-native", tags=["T09"])
async def async_native(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    await asyncio.sleep(seconds)
    return {
        "handler": "async def",
        "execution": "async-native asyncio.sleep",
        "thread_name": threading.current_thread().name,
        "thread_ident": threading.get_ident(),
    }


@app.get("/t09/to-thread", tags=["T09"])
async def to_thread(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    timing = await asyncio.to_thread(_blocking_sleep, seconds)
    return {
        "handler": "async def",
        "execution": "blocking call offloaded with asyncio.to_thread",
        **timing,
    }


@app.get("/t09/sync", tags=["T09"])
def sync_route(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    timing = _blocking_sleep(seconds)
    return {
        "handler": "def",
        "execution": "FastAPI/Starlette dispatched the sync handler to AnyIO",
        **timing,
    }


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


async def run_starvation_probe(
    route: str = "/t09/blocking-inline",
    request_count: int = 20,
    delay_seconds: float = 0.1,
) -> dict[str, object]:
    allowed_routes = {
        "/t09/blocking-inline",
        "/t09/async-native",
        "/t09/to-thread",
        "/t09/sync",
    }
    if route not in allowed_routes:
        raise ValueError(
            "route must be /t09/blocking-inline, /t09/async-native, "
            "/t09/to-thread, or /t09/sync"
        )
    if request_count < 1:
        raise ValueError("request_count must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be nonnegative")

    transport = httpx.ASGITransport(app=app)
    route_latencies: list[float] = []
    health_latencies: list[float] = []
    route_statuses: list[int] = []
    health_statuses: list[int] = []

    async def timed_get(
        client: httpx.AsyncClient,
        path: str,
        latencies: list[float],
        statuses: list[int],
    ) -> None:
        started = time.perf_counter()
        response = await client.get(path)
        latencies.append(time.perf_counter() - started)
        statuses.append(response.status_code)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://t09.local",
        timeout=10,
    ) as client:
        started = time.perf_counter()
        tasks: list[Any] = []
        for _ in range(request_count):
            tasks.append(
                timed_get(
                    client,
                    f"{route}?seconds={delay_seconds}",
                    route_latencies,
                    route_statuses,
                )
            )
            tasks.append(
                timed_get(
                    client,
                    "/t09/health",
                    health_latencies,
                    health_statuses,
                )
            )
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - started

    return {
        "route": route,
        "request_count": request_count,
        "delay_seconds": delay_seconds,
        "elapsed_seconds": round(elapsed, 6),
        "estimated_throughput_rps": round(
            (request_count * 2) / elapsed if elapsed else 0,
            2,
        ),
        "blocking_route": {
            "status_codes": sorted(set(route_statuses)),
            "average_ms": round(statistics.fmean(route_latencies) * 1000, 2),
            "p95_ms": round(percentile(route_latencies, 0.95) * 1000, 2),
        },
        "health": {
            "status_codes": sorted(set(health_statuses)),
            "average_ms": round(statistics.fmean(health_latencies) * 1000, 2),
            "p95_ms": round(percentile(health_latencies, 0.95) * 1000, 2),
        },
    }


async def run_all_starvation_variants(
    request_count: int = 20,
    delay_seconds: float = 0.1,
) -> dict[str, object]:
    results: dict[str, object] = {}
    for route in (
        "/t09/blocking-inline",
        "/t09/async-native",
        "/t09/to-thread",
        "/t09/sync",
    ):
        results[route] = await run_starvation_probe(
            route=route,
            request_count=request_count,
            delay_seconds=delay_seconds,
        )
    return results


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            asyncio.run(run_all_starvation_variants()),
            indent=2,
        )
    )
