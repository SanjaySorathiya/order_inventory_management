# Order & Inventory Management API

A FastAPI capstone for inventory, transactional orders, authentication, and
order tracking. T03 is complete: the main API supports inventory CRUD,
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

## Verification

~~~sh
uv run --locked python -m pytest -q
uv run --locked ruff check app tests exercises
uv run --locked ruff format --check app tests exercises
~~~

See the [verification guide](docs/DEVELOPMENT.md#verification) for setup checks
and [T03 evidence](docs/T03_D3.md#8-verification-and-completion-evidence) for
the 129 passing tests and existing Starlette/HTTPX deprecation warning.

## Documentation

| Document | Contents |
| --- | --- |
| [Development guide](docs/DEVELOPMENT.md) | Setup, settings, verification, and Docker notes. |
| [Task checklist](docs/TODO_TASKS.md) | Learning plan and completion evidence. |
| [Domain and API contract](docs/T01_D1.md) | Agreed final entities, endpoints, and rules. |
| [Runtime architecture](docs/T02_D2.md) | Frameworks, execution models, and request flow. |
| [T03 routes and CRUD](docs/T03_D3.md) | Current behavior, parameter validation, and examples. |
| [Interview revision](docs/FASTAPI_QANDA.md) | Quick questions and answers. |
| [Exercises](exercises/README.md) | Isolated experiments and commands. |
