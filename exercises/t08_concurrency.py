"""Isolated T08 async and synchronous execution exercises."""

import asyncio
import statistics
import threading
import time
from typing import Any

import httpx
from fastapi import FastAPI, Query

app = FastAPI(
    title="T08 concurrency exercises",
    description=(
        "Isolated execution-path demonstrations. Run separately from the capstone API."
    ),
)


def _blocking_sleep(seconds: float) -> dict[str, object]:
    time.sleep(seconds)
    return {
        "thread_name": threading.current_thread().name,
        "thread_ident": threading.get_ident(),
    }


@app.get("/t08/health", tags=["T08"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/t08/async-sleep", tags=["T08"])
async def async_sleep(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    loop = asyncio.get_running_loop()
    await asyncio.sleep(seconds)
    return {
        "handler": "async def",
        "execution": "event loop with asyncio.sleep",
        "thread_name": threading.current_thread().name,
        "thread_ident": threading.get_ident(),
        "loop_id": id(loop),
    }


@app.get("/t08/sync-sleep", tags=["T08"])
def sync_sleep(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    timing = _blocking_sleep(seconds)
    return {
        "handler": "def",
        "execution": "AnyIO worker thread",
        **timing,
    }


@app.get("/t08/async-inline-blocking", tags=["T08"])
async def async_inline_blocking(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    timing = _blocking_sleep(seconds)
    return {
        "handler": "async def",
        "execution": "event loop; synchronous helper ran inline",
        **timing,
    }


@app.get("/t08/slow", tags=["T08"])
async def slow(
    seconds: float = Query(default=0.1, ge=0, le=2),
) -> dict[str, object]:
    await asyncio.sleep(seconds)
    return {"waited_seconds": seconds}


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


async def run_concurrency_probe(
    request_count: int = 20,
    delay_seconds: float = 0.1,
) -> dict[str, object]:
    if request_count < 1:
        raise ValueError("request_count must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be nonnegative")

    transport = httpx.ASGITransport(app=app)
    slow_latencies: list[float] = []
    health_latencies: list[float] = []
    slow_statuses: list[int] = []
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
        base_url="http://t08.local",
        timeout=10,
    ) as client:
        started = time.perf_counter()
        tasks: list[Any] = []
        for _ in range(request_count):
            tasks.append(
                timed_get(
                    client,
                    f"/t08/slow?seconds={delay_seconds}",
                    slow_latencies,
                    slow_statuses,
                )
            )
            tasks.append(
                timed_get(
                    client,
                    "/t08/health",
                    health_latencies,
                    health_statuses,
                )
            )
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - started

    return {
        "request_count": request_count,
        "delay_seconds": delay_seconds,
        "elapsed_seconds": round(elapsed, 6),
        "estimated_throughput_rps": round(
            (request_count * 2) / elapsed if elapsed else 0,
            2,
        ),
        "slow": {
            "status_codes": sorted(set(slow_statuses)),
            "average_ms": round(statistics.fmean(slow_latencies) * 1000, 2),
            "p95_ms": round(percentile(slow_latencies, 0.95) * 1000, 2),
        },
        "health": {
            "status_codes": sorted(set(health_statuses)),
            "average_ms": round(statistics.fmean(health_latencies) * 1000, 2),
            "p95_ms": round(percentile(health_latencies, 0.95) * 1000, 2),
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(asyncio.run(run_concurrency_probe()), indent=2))
