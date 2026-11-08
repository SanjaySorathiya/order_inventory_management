# Development guide

[Project overview](../README.md) | [Task checklist](TODO_TASKS.md)

Detailed setup, configuration, and verification for the capstone.
For the short setup and startup workflow, see the [root README](../README.md).
Run commands from the repository root.

## Development setup

Prerequisites: Python 3.13 and uv on Windows, Linux, or macOS. Use PowerShell on
Windows or Bash/zsh on Linux/macOS. Run these commands from the repository root.

### Windows (PowerShell)

~~~powershell
uv sync --locked

if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}

uv run --locked python --version
uv run --locked python -c "from app.core.config import get_settings; print(get_settings().model_dump())"
~~~

### Linux / macOS (Bash or zsh)

~~~bash
uv sync --locked

if [ ! -e .env ]; then
    cp .env.example .env
fi

uv run --locked python --version
uv run --locked python -c "from app.core.config import get_settings; print(get_settings().model_dump())"
~~~

Both setup examples preserve an existing `.env` file.

### Reproducible environment

The committed `.python-version` selects Python 3.13. `pyproject.toml` declares
application dependencies and a separate `dev` group. `uv.lock` records resolved
versions; `uv sync --locked` installs them without updating that lockfile and
includes development dependencies by default. The local `.venv` is ignored by Git.

### Optional activation

Activation is optional when using `uv run`. For an interactive PowerShell session:

~~~powershell
.\.venv\Scripts\Activate.ps1
~~~

If activation is restricted by your PowerShell policy, use `uv run`; activation
is not required.

For an interactive Bash or zsh session on Linux/macOS:

~~~bash
source .venv/bin/activate
~~~

Run `deactivate` to leave an activated environment in either shell.

### One-time project initialization

The one-time commands used to initialize this existing project were the same
in Windows PowerShell and Linux/macOS Bash or zsh:

~~~sh
uv init --bare --python 3.13 --name order-inventory-mgmt --vcs none
uv python pin 3.13
uv venv --python 3.13
uv add fastapi "uvicorn[standard]" pydantic-settings
uv add --dev pytest httpx ruff
~~~

For an existing checkout, use `uv sync --locked` rather than initializing again.

## Environment configuration

`app/core/config.py` uses `BaseSettings` and `SettingsConfigDict` from
`pydantic_settings`. Call `get_settings()` to retrieve the validated settings.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| OIM_APP_NAME | Order & Inventory Management API | Nonempty application name |
| OIM_ENVIRONMENT | development | One of development, test, production |
| OIM_DEBUG | false | Application debug flag; true/false values are supported |

The loader reads an optional UTF-8 `.env` beside `pyproject.toml`, using a path
relative to the configuration module, so it does not depend on the shell's
working directory. Matching process environment variables take precedence over
file values; declared defaults apply when neither supplies a value. Invalid
values raise a validation error. Unrelated entries in `.env` are ignored.

For example, temporarily override the environment in PowerShell:

~~~powershell
$env:OIM_ENVIRONMENT = "test"
uv run --locked python -c "from app.core.config import get_settings; print(get_settings().environment)"
Remove-Item Env:OIM_ENVIRONMENT
~~~

For Linux/macOS (Bash or zsh), apply the override to one command:

~~~bash
OIM_ENVIRONMENT=test uv run --locked python -c "from app.core.config import get_settings; print(get_settings().environment)"
~~~

This Bash/zsh form leaves the shell's existing environment unchanged afterward.

`get_settings()` caches its result per process. Restart a running process after
changing settings; tests clear the cache when changing the environment.
The environment label does not automatically change other settings: selecting
production does not by itself configure deployment or authentication.

Commit `.env.example`, `pyproject.toml`, `.python-version`, and `uv.lock`.
Keep `.env`, other local dotenv variants, credentials, and `.venv` out of Git.
The example file contains no credentials. Database and signing settings will be
introduced with their corresponding features.

## Verification

These commands work in Windows PowerShell and Linux/macOS Bash or zsh:

~~~sh
uv lock --check --offline
uv pip check
uv run --locked python -m pytest -q
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
~~~

The configuration tests verify defaults without a dotenv file, process-variable
precedence over dotenv values, and rejection of invalid environment values.
The synchronous health smoke test checks the status, JSON media type, and exact
payload using an isolated application and explicit test settings. Pytest
configuration in `pyproject.toml` limits default collection to `tests/`.

Recorded results and the current Starlette/HTTPX deprecation warning are in the
[T02 verification notes](T02_D2.md#7-completion-evidence-and-interview-recall).

## API documentation

The [README's API URLs](../README.md#run-the-api) link to the health endpoint,
Swagger UI, ReDoc, and OpenAPI JSON. The health endpoint checks liveness without
authentication, database, or external-service checks. Readiness remains planned.

The default documentation UIs load assets from external CDNs. The
[T02 runtime notes](T02_D2.md) explain the request flow and documentation
inspection steps.

## Docker later

For Docker later, supply the same `OIM_*` variables through the container
environment. Build a fresh environment from the committed manifest and lockfile
inside the image. Recreate `.venv` for each operating system or container rather
than copying a Windows, Linux, or macOS environment between installations.
No Docker files or container services are required for this stage.

## References

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).
- [Python virtual environment activation](https://docs.python.org/3.13/library/venv.html#how-venvs-work).
