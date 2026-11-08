# Order & Inventory Management API

A FastAPI capstone for inventory, transactional orders, authentication, and
order tracking. T02 is complete: the app serves a public health endpoint and API
documentation. Business endpoints are planned in the [task checklist](docs/TODO_TASKS.md).

## Development setup

Prerequisites: Python 3.13 and uv. Run commands from the repository root.

~~~sh
uv sync --locked
~~~

Create `.env` from the safe example if it does not already exist.

Windows PowerShell:

~~~powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
~~~

Linux/macOS (Bash or zsh):

~~~bash
if [ ! -e .env ]; then
    cp .env.example .env
fi
~~~

`uv run` uses the project environment without activation. See the
[development guide](docs/DEVELOPMENT.md) for configuration and setup details.

## Run the API

~~~sh
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
~~~

| URL | Purpose |
| --- | --- |
| [`/health`](http://127.0.0.1:8000/health) | Returns 200 with `{"status":"ok"}`. |
| [`/docs`](http://127.0.0.1:8000/docs) | Swagger UI: expand GET /health, then Try it out and Execute. |
| [`/redoc`](http://127.0.0.1:8000/redoc) | Alternative API reference. |
| [`/openapi.json`](http://127.0.0.1:8000/openapi.json) | Generated OpenAPI contract. |

The root URL `/` returns 404 because it has no route. The API entry point is
`app.main:app`; the root `main.py` is a learning script.
`--reload` is for development. Stop the server with Ctrl+C.

## Verification

~~~sh
uv run --locked python -m pytest -q
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
~~~

See the [full verification guide](docs/DEVELOPMENT.md#verification) for lockfile
checks, test coverage, and recorded results.

## Documentation

| Document | Contents |
| --- | --- |
| [Development guide](docs/DEVELOPMENT.md) | Detailed setup, environment settings, verification, and Docker notes. |
| [Task checklist](docs/TODO_TASKS.md) | Ordered learning plan and links to completion evidence. |
| [Domain and API contract](docs/T01_D1.md) | Agreed entities, endpoints, and business rules from T01. |
| [Runtime architecture](docs/T02_D2.md) | Framework comparisons, execution models, and the request-flow diagram. |
| [Interview revision](docs/FASTAPI_QANDA.md) | Quick questions and answers. |
| [Exercises](exercises/README.md) | Scope of isolated learning experiments. |
