# Order & Inventory Management API

A FastAPI capstone for inventory, transactional orders, authentication, and
order tracking. T04 is complete: isolated request-format exercises and the
initial HTTP response contract are covered. The main API supports inventory CRUD,
filtering, sorting, and pagination with temporary in-memory storage.
See the [task checklist](docs/TODO_TASKS.md) for later stages.

Inventory starts empty and resets on reload/restart. Writes are unauthenticated
in development/test and disabled in production until T15-T16. Auth/order routes
return 501; inactive inventory access awaits admin authentication.

## Development setup

Prerequisites: Python 3.13 and uv. Run from the repository root.

~~~sh
uv sync --locked
~~~

Create .env from the safe example if it does not already exist.

Windows PowerShell:

~~~powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
~~~

Linux/macOS Bash/zsh:

~~~bash
if [ ! -e .env ]; then
    cp .env.example .env
fi
~~~

uv run uses the project environment without activation. See the
[development guide](docs/DEVELOPMENT.md) for configuration and setup details.

## Run the API

~~~sh
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
~~~

| URL | Purpose |
| --- | --- |
| [/health](http://127.0.0.1:8000/health) | Public liveness; status: ok. |
| [/api/v1/inventory](http://127.0.0.1:8000/api/v1/inventory) | Catalog; use POST in /docs to create the first item. |
| [/docs](http://127.0.0.1:8000/docs) | Swagger UI and interactive CRUD. |
| [/redoc](http://127.0.0.1:8000/redoc) | Alternative API reference. |
| [/openapi.json](http://127.0.0.1:8000/openapi.json) | Generated OpenAPI contract. |

The root URL / returns 404. The entry point is app.main:app.
--reload is for local development. Stop with Ctrl+C.
The [T03 guide](docs/T03_D3.md#7-run-and-demonstrate-the-main-api) contains a
complete PowerShell CRUD demonstration and isolated parameter exercises.

## Request-format exercises

Run T04 separately from the main API:

~~~sh
uv run --locked uvicorn exercises.t04_requests:app --host 127.0.0.1 --port 8002 --reload
~~~

Visit http://127.0.0.1:8002/docs for headers, cookies, JSON/forms, controlled
.txt uploads up to 2 MiB, and HTTPException examples. See the
[T04 guide](docs/T04_D4.md) for examples and the HTTP response contract.

## Verification

~~~sh
uv run --locked python -m pytest -q
uv run --locked ruff check app tests exercises
uv run --locked ruff format --check app tests exercises
~~~

See the [verification guide](docs/DEVELOPMENT.md#verification) for setup checks
and [T04 evidence](docs/T04_D4.md#7-verification-and-completion-evidence) for
the 169 passing tests and existing Starlette/HTTPX deprecation warning.

## Documentation

| Document | Contents |
| --- | --- |
| [Development guide](docs/DEVELOPMENT.md) | Setup, settings, verification, and Docker notes. |
| [Task checklist](docs/TODO_TASKS.md) | Learning plan and completion evidence. |
| [Domain and API contract](docs/T01_D1.md) | Agreed final entities, endpoints, and rules. |
| [Runtime architecture](docs/T02_D2.md) | Frameworks, execution models, and request flow. |
| [T03 routes and CRUD](docs/T03_D3.md) | Current behavior, parameter validation, and examples. |
| [T04 inputs and HTTP](docs/T04_D4.md) | Headers, cookies, forms/uploads, cleanup, and HTTP contracts. |
| [Interview revision](docs/FASTAPI_QANDA.md) | Quick questions and answers. |
| [Exercises](exercises/README.md) | Isolated experiments and commands. |
