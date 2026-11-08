# FastAPI Interview Q&A: Quick Revision

- Project: Order & Inventory Management API
- Updated: 2026-11-08
- Coverage: T01 setup and the completed T02 runtime skeleton.

Use each short answer as a starting point for a 30-60 second explanation.
The project has environment configuration, a running ASGI app, and six tests
covering configuration and health. See [T02 runtime revision](T02_D2.md) for
framework comparisons, execution models, and the request-flow diagram.
Orders, database transactions, authentication, and tracking below are agreed
design decisions; their implementations belong to later tasks.

Navigation: [Environment and dependencies](#1-environment-and-dependencies),
[Uvicorn](#2-fastapi-and-uvicorn), [Configuration](#3-environment-configuration),
[Python](#4-python-prerequisites), [HTTP](#5-http-contracts),
[Project design](#6-capstone-design-decisions), [Final recall](#7-final-recall).

## 1. Environment and dependencies

### Q01. What jobs make up Python project setup?

Select a Python version, create an isolated environment, declare dependencies,
resolve their versions, and install them. FastAPI does not mandate one setup
tool: `venv + pip` and uv are both valid workflows. This project uses uv.

**Interview point:** Creating a virtual environment does not install FastAPI.

### Q02. Why create a virtual environment?

It isolates a project's installed packages from other projects and the base
Python installation. Two APIs can therefore use different dependency versions.
The environment directory is disposable; recreate it from recorded dependencies
instead of committing it. See the [Python venv guide](https://docs.python.org/3.13/library/venv.html).

### Q03. What is the traditional venv + pip workflow?

Windows PowerShell:

~~~powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\Activate.ps1
python -m pip install -r requirements.txt
~~~

Linux/macOS, Bash or zsh, with Python 3.13 available:

~~~bash
python3.13 -m venv .venv313
source .venv313/bin/activate
python -m pip install -r requirements.txt
~~~

Both examples assume `requirements.txt` already exists. The folder name
`.venv313` is a convention, not a Python feature; the activation path must match
the actual directory. Shell-specific activation follows the
[venv activation reference](https://docs.python.org/3.13/library/venv.html#how-venvs-work).

### Q04. How does the uv workflow compare?

For a new project, from its empty project directory, these commands work in
Windows PowerShell and Linux/macOS Bash or zsh:

~~~sh
uv init --bare --python 3.13 --name order-inventory-mgmt --vcs none
uv python pin 3.13
uv venv --python 3.13
uv add fastapi "uvicorn[standard]" pydantic-settings
uv add --dev pytest httpx ruff
~~~

The first three create project metadata, record Python selection, and create
`.venv`. The two `uv add` commands declare, resolve, and install packages.
`--bare` avoids an example application scaffold; `--vcs none` skips Git
initialization. See the [uv project guide](https://docs.astral.sh/uv/guides/projects/).

For an existing checkout with a committed lockfile:

~~~sh
uv sync --locked
uv run --locked python --version
~~~

Initialize once per new project; do not repeat initialization after every clone.

### Q05. What is .python-version?

It records the interpreter request used by uv. Here, `3.13` selects the Python
3.13 series; it does not pin one patch release or change the machine's global
Python. An exact request such as `3.13.17` is more specific.
See [uv Python selection](https://docs.astral.sh/uv/concepts/python-versions/).

### Q06. What is pyproject.toml?

It is standard Python project configuration. Our file declares the project
name, application version, supported Python range, runtime dependencies, and
a development dependency group. Tools can also keep configuration in it.

`version = "0.1.0"` is the application version, not the Python version.
The format is explained in the [Python packaging guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

### Q07. How do .python-version and requires-python differ?

| Setting | Meaning in this project |
| --- | --- |
| `.python-version: 3.13` | Select a 3.13 interpreter for development. |
| `requires-python = ">=3.13"` | Declare that 3.13 and later are allowed. |

The range does not force every command to use 3.13, and it does not prove the
application was tested on every later Python release. Selection and declared
compatibility are separate concerns.

### Q08. What does uv.lock solve?

It records resolved versions of direct and indirect dependencies, including
platform conditions. It makes repeated installation predictable within
compatible platforms and interpreters. A manifest usually allows version ranges;
the lockfile records the chosen resolution.

Do not hand-edit the lockfile. Update it through uv and review the changes.
See [uv project files](https://docs.astral.sh/uv/concepts/projects/layout/).

### Q09. Is requirements.txt automatically less reproducible?

No. It is a pip installation input, and it can contain exact pins and hashes.
An unpinned list can resolve differently later; a complete pinned dependency
set gives stronger repeatability. A bare `pip freeze` snapshot does not explain
which packages were direct dependencies or development-only tools.
See [pip requirements files](https://pip.pypa.io/en/stable/reference/requirements-file-format/).

This project manages dependencies through `pyproject.toml` and `uv.lock`
rather than maintaining a second list manually.

### Q10. Why separate application and development dependencies?

Application dependencies are needed to run features. Development dependencies
support testing or code checks. Our current split is:

| Group | Packages and purpose |
| --- | --- |
| Application | FastAPI: API; Uvicorn: server; Pydantic Settings: configuration. |
| Development | pytest: tests; HTTPX: API testing client; Ruff: lint/format. |

Use `uv add package-name` for application dependencies and
`uv add --dev package-name` for the development group.
Development dependencies are included by default during `uv sync`; use
`uv sync --locked --no-dev` when an installation should exclude that group.
See [uv dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies).

HTTPX will also be used for outbound application requests in T10; declare it as
an application dependency when application code starts using it.

### Q11. How do add, lock, sync, run, and check differ?

| Command | Job |
| --- | --- |
| `uv add package-name` | Declare a dependency, resolve, and install. |
| `uv lock` | Resolve/update the lockfile without installing packages. |
| `uv sync --locked` | Check lock freshness and synchronize the environment. |
| `uv run --locked python main.py` | Check/sync, then execute in the environment. |
| `uv lock --check --offline` | Check lock freshness without network access. |
| `uv pip check` | Check installed-package dependency compatibility. |

`--locked` fails when a manifest change requires a lockfile update.
`--frozen` uses the existing lockfile without checking its freshness; it is
not the same guarantee. These checks do not replace application tests.
See [uv command reference](https://docs.astral.sh/uv/reference/cli/).

### Q12. Must I activate .venv before using uv?

No. `uv run` selects the project environment. Activation is useful for an
interactive shell, but is optional.

| Shell | Optional activation for this project's .venv |
| --- | --- |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Linux/macOS Bash or zsh | `source .venv/bin/activate` |

`source venv/bin/activate` is not a PowerShell command. If PowerShell activation
is restricted, use `uv run`; the environment still works.

### Q13. Which setup files should be committed?

Commit `pyproject.toml`, `uv.lock`, `.python-version`, and `.env.example`.
Keep `.venv`, local `.env` variants, credentials, and generated caches out of Git.
Our [.gitignore](../.gitignore) keeps the example dotenv file available to commit.

When moving to Linux, macOS, another machine, or Docker, recreate the environment
from these files. An environment contains installation-specific interpreter and
script paths; copying its directory is unreliable.

## 2. FastAPI and Uvicorn

### Q14. What is the difference between FastAPI, Uvicorn, and uv?

FastAPI is the application framework. Uvicorn is the ASGI server that runs the
application and handles network traffic. uv manages Python environments and
dependencies. Similar names do not imply the same responsibility.

An ASGI server can run a compatible application; it does not replace the
framework's routes or validation. See [Uvicorn's introduction](https://uvicorn.dev/).

### Q15. What does uvicorn[standard] mean?

It installs the same Uvicorn package plus its `standard` dependency extra.
Square brackets select optional dependencies, not another server edition.

Plain `uvicorn` includes `h11` and `click`. The standard extra adds:

| Dependency | Purpose |
| --- | --- |
| httptools | Alternative HTTP/1.1 parser. |
| uvloop | Alternative event loop on supported platforms. |
| watchfiles | File watching for reload. |
| websockets | WebSocket protocol implementation. |
| python-dotenv | Support for Uvicorn's --env-file option. |
| PyYAML | YAML logging configuration support. |

Install with `uv add "uvicorn[standard]"`. Quoting the brackets also avoids
shell glob expansion, especially in zsh.
The list follows [Uvicorn installation guidance](https://uvicorn.dev/installation/).

### Q16. Does standard enable uvloop on Windows?

No. uvloop is excluded on Windows, where Uvicorn uses the built-in asyncio
event loop under its normal automatic selection. Other applicable standard
extras can still be installed.
See [Uvicorn platform settings](https://uvicorn.dev/settings/#implementation).

### Q17. Does plain Uvicorn support reload, and does standard enable it automatically?

Plain Uvicorn supports basic polling of Python-file changes with `--reload`.
With watchfiles installed, reload supports richer include/exclude file patterns.
Installing standard alone does not turn reload on; the flag still controls it.

The current development launch command is:

~~~sh
uv run --locked uvicorn app.main:app --reload
~~~

It means import `app` from the module `app.main`. T02 provides that ASGI
application and `GET /health`; the root `main.py` remains a learning script.
The launch syntax is unchanged by installing extras.
See [Uvicorn reload options](https://uvicorn.dev/settings/#development).

## 3. Environment configuration

### Q18. Why use environment-based configuration?

It separates deploy-specific values from source code. The same application can
receive settings from local files on a workstation or injected variables in a
container, without rewriting the settings class. Environment variables arrive
as strings; typed settings parse and validate them.
See [FastAPI settings](https://fastapi.tiangolo.com/advanced/settings/).

### Q19. Where does BaseSettings come from?

In our Pydantic v2 setup, import it from `pydantic_settings`:

~~~python
from pydantic_settings import BaseSettings, SettingsConfigDict
~~~

`BaseSettings` loads configuration from settings sources. A `BaseModel`
primarily validates supplied model data; it does not, by itself, provide the
same settings-source loading.
See [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

### Q20. What do the options in our SettingsConfigDict do?

| Option | Behavior in our configuration |
| --- | --- |
| env_prefix="OIM_" | Map app_name to OIM_APP_NAME, and likewise for other fields. |
| env_file | Read the optional project-root .env file. |
| env_file_encoding="utf-8" | Decode that file as UTF-8. |
| str_strip_whitespace=True | Trim outer whitespace from string values. |
| extra="ignore" | Allow unrelated dotenv entries. |

The absolute path is derived from `__file__`; changing the shell's working
directory does not change which dotenv file is selected.
Unknown dotenv entries are ignored, so a misspelled name may go unnoticed.
See our [settings implementation](../app/core/config.py).

### Q21. Which setting source wins?

For the normal, argument-free `get_settings()` call in this project:

~~~text
Process environment > project-root .env > field defaults
~~~

Explicit constructor values, such as `Settings(debug=True)`, take priority
over those environment sources under the default settings-source ordering.
Tests can use `_env_file=...` to select a temporary file or `_env_file=None`
to disable dotenv loading. These behaviors follow the
[Pydantic settings-source rules](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#field-value-priority).

### Q22. How do .env and .env.example differ?

`.env` holds local settings and is ignored by Git. `.env.example` is a committed
template with safe examples. Neither a virtual environment nor the existence of
a dotenv file automatically loads application configuration; a loader must read
it. Our Settings class supplies that loader.

Copy only when a local file does not already exist.

Windows PowerShell:

~~~powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
~~~

Linux/macOS, Bash or zsh:

~~~bash
if [ ! -e .env ]; then
    cp .env.example .env
fi
~~~

### Q23. How do I temporarily override a setting?

Windows PowerShell:

~~~powershell
$code = 'import app.core.config as config; print(config.get_settings().environment)'
$env:OIM_ENVIRONMENT = "test"
uv run --locked python -c $code
Remove-Item Env:OIM_ENVIRONMENT
~~~

This sets a value for the shell and its child processes, then removes it.
If that variable had a previous value, save and restore it instead of removing it.

Linux/macOS, Bash or zsh:

~~~bash
code='import app.core.config as config; print(config.get_settings().environment)'
OIM_ENVIRONMENT=test uv run --locked python -c "$code"
~~~

The Bash/zsh OIM_ENVIRONMENT assignment applies only to that command. Both examples print
`test`; they are different shell syntaxes for passing an environment variable.

### Q24. Why is get_settings decorated with lru_cache?

It reuses the settings object after the first load in that process.
Changing `.env` or process variables later does not refresh the cached object.
Restart the process, or call `get_settings.cache_clear()` in a controlled test.

Each worker process has its own cache. This is not a cross-worker shared store.
Tests clear the cache and isolate environment variables to prevent state from
leaking between cases. See [functools caching](https://docs.python.org/3.13/library/functools.html#functools.lru_cache).

### Q25. What validation does our settings class enforce?

`environment` accepts development, test, or production through `Literal`.
`debug` is a boolean; a value such as `"not-a-boolean"` is rejected.
The application name is trimmed and must remain nonempty through `Field`.

Setting `OIM_ENVIRONMENT=production` only changes that label. It does not
automatically configure deployment, switch debug off, or implement authentication.
See [config.py](../app/core/config.py).

### Q26. Does Uvicorn's --env-file replace application settings validation?

No. That option loads values into the environment; the application still needs
to interpret and validate its settings. Our BaseSettings loader already reads
the local dotenv file, so `--env-file` is not required for that path.

Uvicorn's dotenv option is intended for application configuration; it does not
read `UVICORN_*` server options from that file.
See [Uvicorn configuration](https://uvicorn.dev/settings/#configuration-methods).

### Q27. What do our tests demonstrate?

There are five configuration cases: defaults with no dotenv file, process values
overriding dotenv values, and rejection of an invalid environment, an invalid
boolean, and a blank name. T02 adds a synchronous TestClient smoke test for
the health status, JSON content type, and exact payload: six passing cases in
total. They do not prove checkout or authentication works.

pytest runs tests; HTTPX supports HTTP-client/API-test work; Ruff lints and formats
code. Neither the configuration tests nor the in-process health smoke test
needs a listening HTTP server. See [test_config.py](../tests/test_config.py),
[test_health.py](../tests/test_health.py), and the
[T02 verification notes](T02_D2.md#7-completion-evidence-and-interview-recall).

### Q28. How can I verify the current setup?

These commands are shared across Windows PowerShell and Linux/macOS Bash/zsh:

~~~sh
uv lock --check --offline
uv pip check
uv run --locked python -m pytest -q
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
~~~

A valid lockfile, installed-package compatibility, passing tests, and clean
lint/format results answer different questions. None alone proves the entire
application is correct. See [verification instructions](DEVELOPMENT.md#verification).

## 4. Python prerequisites

### Q29. Do Python type hints enforce runtime validation?

No. A function annotated with `quantity: int` can still receive a different
runtime type unless code or a validation library rejects it. Type checkers help
before runtime; Pydantic can validate values at runtime.

`int | None` permits None. Whether an argument can be omitted depends on its
default, not merely on including None in its annotation.
See [Python typing](https://docs.python.org/3.13/library/typing.html).

### Q30. What is a decorator?

It takes a callable and produces the callable bound to the function name.
`@decorator` is conceptually `function = decorator(function)`.
A route decorator registers a handler; registration does not itself execute the
handler body. A wrapper may add behavior when calls occur.

`functools.wraps` helps preserve the wrapped function's metadata.
See [Python function definitions](https://docs.python.org/3.13/reference/compound_stmts.html#function-definitions).

### Q31. Why use a context manager and finally?

A context manager defines resource entry and exit around a `with` block.
A cleanup action in `finally` runs when control leaves the protected code,
including normal Python exception paths. Async context managers use
`async with` for asynchronous acquisition and cleanup.

This supports session/client ownership; it does not guarantee cleanup after
a forced process termination. See [contextlib](https://docs.python.org/3.13/library/contextlib.html).

### Q32. What is a generator, and how does it relate to cleanup?

A function containing `yield` creates a generator when called. Its body runs
as the generator advances, producing values lazily. It is not automatically
a context manager. `@contextmanager` can adapt a one-yield generator into one.

The project demonstration checks lazy validation and exception-safe cleanup.
See [the T01 example](T01_D1.md#demonstration) and the
[Python generator tutorial](https://docs.python.org/3.13/tutorial/classes.html#generators).

## 5. HTTP contracts

### Q33. How do GET, POST, PUT, PATCH, and DELETE differ?

GET reads a representation. POST creates a resource or performs an operation.
PUT replaces writable state; PATCH applies a specified partial change.
DELETE removes a resource from active use according to its contract.

Here, inventory PUT requires every mutable field, PATCH preserves omitted fields,
and DELETE deactivates the item while retaining order history. Those are project
choices. HTTP method semantics are defined in
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-9) and
[PATCH semantics](https://www.rfc-editor.org/rfc/rfc5789.html).

### Q34. Which status codes should I recall?

| Code | Use in this contract |
| --- | --- |
| 200 | Successful read/update with a representation. |
| 201 | Created resource; include Location in our API. |
| 204 | Successful operation with no response body. |
| 401 | Missing/invalid authentication; include WWW-Authenticate. |
| 403 | Caller lacks permission. |
| 404 | Resource absent or deliberately hidden. |
| 409 | Business conflict, such as insufficient stock. |
| 422 | Invalid request shape/value. |
| 500 / 503 | Unexpected server failure / readiness unavailable. |

A missing database row is different from an invalid identifier.
These choices build on [HTTP status semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-15).

### Q35. What is idempotence, and can checkout be retried safely?

It means repeated identical requests have the same intended effect as one.
It does not require identical response codes. PUT and DELETE are idempotent by
their method semantics; PATCH depends on its operation; POST generally is not.

Our repeated same-status assignment is a no-op, including cancellation.
Checkout POST has no idempotency-key guarantee yet. A lost response may leave a
committed order, so retrying can duplicate it; this baseline requires operator
assistance to reconcile an unknown order ID.

## 6. Capstone design decisions

The following answers describe the [T01 contract](T01_D1.md), not implemented
database, authorization, or streaming behavior.

### Q36. What are the four entities and their relationships?

User owns many Orders. Order contains one or more OrderItems. Each OrderItem
references an InventoryItem and stores its purchased quantity and price snapshot.
An InventoryItem can appear in many historical order lines.

IDs identify rows; normalized, immutable SKU values uniquely identify catalog
items. Deactivation keeps historical references valid.

### Q37. Why use integer money and snapshot order prices?

Integer minor units avoid binary floating-point rounding for monetary arithmetic.
This project uses INR: 12500 means INR 125.00. The server computes line and order
totals from stored catalog prices, never from client-supplied totals.

Order lines snapshot SKU, name, and price so catalog edits do not rewrite
purchase history. Example: two units at 12500 produce a 25000 total.

### Q38. How should checkout avoid partial writes and overselling?

Create the order/lines and deduct all stock in one transaction. Any missing,
inactive, or insufficient-stock line rejects the whole checkout and rolls it back.
Validate positive quantities and reject duplicate order lines.

The planned PostgreSQL implementation locks inventory rows in ascending ID order
before checking and deducting stock. Competing catalog edits and cancellation
must follow compatible locking rules. Transactions alone do not prove that a
read-check-write sequence prevents concurrent overselling.

### Q39. What is the order lifecycle, including cancellation?

~~~text
pending -> processing -> shipped -> delivered
pending -> cancelled
processing -> cancelled
~~~

Stock is deducted when checkout creates pending. Cancellation restores it once,
atomically with the status change. Delivered and cancelled are terminal.
Assigning the current status is a 200 no-op; a different disallowed transition
returns 409. Only an admin changes status in this design.

### Q40. Who can access which resources?

Anonymous callers can read active inventory and health. Active users can order
for themselves; customers can read/track their own orders. Admins manage inventory,
read/track any order, and perform allowed status transitions.

The owner comes from authenticated identity, not a submitted user ID.
Another customer's order returns 403 in this contract. Public user output excludes
password hashes and internal account metadata.

### Q41. Why choose SSE for tracking, and what are its limits?

Order updates flow server to client, so SSE fits the one-way requirement.
The planned browser client uses streaming fetch to send a bearer header;
native EventSource has no arbitrary-header option.
See [the EventSource standard](https://html.spec.whatwg.org/multipage/server-sent-events.html).

The design sends a current snapshot and committed status changes with versions.
Delivery is live-only; reconnect gets a new snapshot without guaranteed replay.
A process-local broadcaster requires one worker for its stated delivery behavior;
multiple workers need shared transport. Do not hold a database session while
waiting for stream events.

## 7. Final recall

### Q42. How can I explain this project's setup in one minute?

"I use uv with Python 3.13. The version file selects the interpreter, the
pyproject declares dependencies and their groups, and the lockfile records the
resolution. I recreate an isolated environment with locked sync and run commands
through uv. Typed settings read local dotenv values or injected environment
variables, with process values taking precedence in the normal loading path.
Tests verify configuration precedence and invalid values. The domain contract
defines atomic checkout and access rules; those features are the next work."

Adapt the final sentence as implementation progresses; distinguish designed,
implemented, and tested behavior.

### Common interview traps

- A virtual environment does not install the API framework.
- Application version, Python selection, and supported Python range are different.
- Installing an extra does not automatically enable its runtime flags.
- Standard Uvicorn does not imply uvloop support on Windows.
- Basic reload also exists without watchfiles.
- A dotenv file needs a loader; cached settings do not refresh automatically.
- An environment label is not a complete production configuration.
- An ignored typo can cause a default to be used silently.
- A database transaction needs a concurrency strategy to prevent overselling.
- A committed checkout is not automatically safe to repeat.
- Never print all future settings blindly after adding secrets to the model.
- Implemented configuration tests do not prove planned API features work.

## Maintaining the revision guide and exporting later

Append new numbered questions as later tasks teach new topics. Keep answers short,
include one useful example or pitfall, and link to the relevant implementation.
Revise the progress statement and project story as features become demonstrable.

This guide uses ordinary Markdown headings, short paragraphs, narrow tables,
and fenced commands. It needs no interactive elements or diagram renderer.
For the final PDF, render Markdown in a viewer that supports printing, choose
A4 or Letter portrait, and preview code wrapping and page breaks before saving.
Keep source links clickable and avoid splitting question headings from answers.
No PDF or converter installation is required at the present stage.

Related project documents: [project README](../README.md),
[development guide](DEVELOPMENT.md),
[task checklist](TODO_TASKS.md), [T01 summary](T01_D1.md), and
[T02 runtime revision](T02_D2.md).
