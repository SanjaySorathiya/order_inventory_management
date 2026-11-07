# TODO Tasks: Order & Inventory Management API

## How to use this checklist

- Complete T01 through T21 in order. Day labels are planning targets; finish a prerequisite before moving to its dependent work.
- Introduce tests alongside each feature, then consolidate the suite in T20.
- Use separate exercises for special request formats and intentionally broken examples that do not belong in the capstone API.
- Mark an item complete only when its implementation, experiment, or explanation can be demonstrated.
- A WebSocket **or** SSE implementation is required. Implementing both, or operating an external task queue, is an extension.
- Verify current official package guidance before choosing versions, settings imports, password hashing libraries, or production worker commands from the source examples.

## Week 1: Foundations, request contracts, and validation

### T01 - Day 1: Define the capstone and prepare the environment

- [x] Review Python type hints, decorators, context managers, generators, and HTTP methods/status codes; list any prerequisite gaps.
- [x] Define User, InventoryItem, Order, and OrderItem entities, their relationships, and the permitted order status transitions.
- [x] Define business rules: positive quantities, nonnegative stock, unique item identifiers, server-calculated totals, insufficient-stock behavior, and who may read or modify each resource.
- [x] Write an endpoint contract covering login, inventory listing/detail/administration, order creation/detail, health checks, and order tracking.
- [x] Create a Python virtual environment and a reproducible dependency manifest; separate application and development dependencies.
- [x] Add environment-based configuration and an example environment file without real credentials; document setup commands in a README.

**T01 complete:** All six items are documented in [T01_D1.md](T01_D1.md). Python 3.13/uv, separate dependency groups, the lockfile, [Windows PowerShell and Linux/macOS Bash/zsh setup instructions](../README.md#development-setup), and validated environment configuration are ready. Five configuration tests and Ruff lint/format checks pass. Continue with T02.

**Deliverable:** An agreed API contract and a reproducible local development environment.

### T02 - Day 2: Understand the runtime and scaffold a working app

- [ ] Explain the responsibilities of FastAPI, Starlette, Pydantic, and an ASGI server; compare FastAPI with Flask and Django.
- [ ] Diagram a request from server through middleware, routing, dependencies, validation, handler execution, serialization, and response.
- [ ] Compare ASGI and WSGI capabilities, concurrency versus parallelism, and event-loop versus thread/process execution without assuming every server uses the same model.
- [ ] Create the application layout: `app/main.py`, `api/deps.py`, `api/v1/`, `core/`, `models/`, `schemas/`, a service layer, `tests/`, and `exercises/`.
- [ ] Start a minimal app with Uvicorn, add a health endpoint, and inspect `/docs`, `/redoc`, and `/openapi.json`.
- [ ] Configure pytest and add a synchronous `TestClient` smoke test for the health endpoint.

**Deliverable:** A running skeleton, a passing smoke test, and a runtime architecture diagram.

### T03 - Day 3: Build modular routes and parameter validation

- [ ] Create and register versioned auth, inventory, and order routers using `APIRouter`, prefixes, and tags.
- [ ] Practice GET, POST, PUT, PATCH, and DELETE; distinguish full replacement, partial updates, and deletion semantics.
- [ ] Add typed path parameters and `Path()` constraints for resource identifiers.
- [ ] Add required and optional query parameters; distinguish a missing default from an explicitly nullable value.
- [ ] Implement validated filtering, sorting, and bounded pagination for inventory lookups using `Query()`.
- [ ] Test invalid identifiers, query bounds, missing required parameters, and static-versus-dynamic route ordering.

**Deliverable:** Modular routes with predictable parameter binding and validation behavior.

### T04 - Day 4: Handle special inputs and establish HTTP error contracts

- [ ] Practice `Header()` and `Cookie()`; demonstrate how Python parameter underscores map to HTTP header hyphens.
- [ ] Handle form submissions with `Form()` and install the multipart dependency needed for form/file exercises.
- [ ] Implement a controlled `UploadFile` exercise with size/type checks and cleanup; explain in-memory spooling and rollover to disk.
- [ ] Distinguish JSON request bodies from form and multipart payloads.
- [ ] Establish success/error status codes, including 201 for creation, 204 with no response body, 404 for missing resources, and 409 for business conflicts.
- [ ] Raise `HTTPException` for expected failures and test its status, detail, and optional headers.

**Deliverable:** Request-format exercises and an initial, documented HTTP response contract.

### T05 - Day 5: Design Pydantic v2 domain schemas

- [ ] Create separate create, update, and read schemas for inventory and orders, including nested order lines.
- [ ] Define user/login input and public user output schemas; keep password hashes and internal fields out of public models.
- [ ] Apply `Field()` constraints for identifiers, quantities, lengths, and monetary values; choose an explicit money representation.
- [ ] Decide where coercion is acceptable and where strict validation or rejection of extra fields is required.
- [ ] Configure models with `ConfigDict`; prepare ORM-compatible read schemas where needed.

**Deliverable:** Typed, separated input/output contracts for the domain.

### T06 - Day 6: Implement validators and study validation failures

- [ ] Add `@field_validator` for field normalization and `@model_validator` for cross-field rules.
- [ ] Define how duplicate order lines are handled and validate empty orders, invalid quantities, and inconsistent input.
- [ ] Use `model_dump()`, including `exclude_unset=True` where appropriate for PATCH; explain the corresponding Pydantic v1 patterns.
- [ ] Trigger and inspect structured 422 responses, including error locations and messages.
- [ ] Keep database-dependent rules, such as stock availability and uniqueness conflicts, in the service/transaction layer.
- [ ] Add targeted schema tests for valid, invalid, coercible, and strict inputs.

**Deliverable:** Validated domain inputs with observable and tested failure cases.

### T07 - Day 7: Enforce output filtering and review Week 1

- [ ] Apply `response_model` to public endpoints and verify nested output serialization.
- [ ] Demonstrate that password hashes, internal flags, and private metadata are excluded from responses.
- [ ] Test the difference between invalid client input and an invalid server response.
- [ ] Add endpoint summaries, descriptions, examples, response codes, and tags to the generated API documentation.
- [ ] Check the implemented schemas and routes against the endpoint contract.
- [ ] Explain request binding, validation, response filtering, and ASGI/WSGI trade-offs aloud.

**Week 1 gate:** The skeleton runs, request/schema exercises pass, sensitive fields are filtered, and the API contract is documented.

## Week 2: Concurrency, dependencies, and persistence

### T08 - Day 8: Compare asynchronous and synchronous execution

- [ ] Build isolated `async def` and `def` route exercises and observe event-loop versus AnyIO worker-thread execution.
- [ ] Explain that ordinary synchronous helper calls inside an async handler are not automatically moved to a worker thread.
- [ ] Compare cooperative I/O concurrency with CPU-bound work and multi-process parallelism.
- [ ] Run a repeatable concurrent-request experiment against a slow route and a health route.
- [ ] Record baseline latency and throughput observations without assuming that adding `async` automatically improves performance.

**Deliverable:** A reproducible concurrency experiment with an explanation of its execution paths.

### T09 - Day 9: Diagnose event-loop starvation

- [ ] Reproduce diagnostic scenario 1 by placing a blocking call inside an isolated async route.
- [ ] Observe its effect on concurrent requests and health-check responsiveness.
- [ ] Replace the call with an async-native equivalent and repeat the same experiment.
- [ ] Repeat with `asyncio.to_thread()` or `run_in_threadpool()`; compare with a synchronous route.
- [ ] Explain threadpool capacity limits and when CPU-intensive work belongs in a separate worker process.

**Deliverable:** Before/after evidence and a diagnosis of event-loop starvation.

### T10 - Day 10: Apply non-blocking I/O patterns

- [ ] Use `httpx.AsyncClient` for outbound HTTP calls and configure explicit timeouts and connection limits.
- [ ] Compare per-call client creation with a reusable client; prepare to move client ownership into application lifespan.
- [ ] Handle upstream timeouts and failures through the API error contract.
- [ ] Audit async paths for blocking database, HTTP, file, and sleep calls.
- [ ] Keep slow external I/O outside database transactions where possible and document the reason.

**Deliverable:** Non-blocking outbound I/O with explicit failure behavior.

### T11 - Day 11: Build dependency graphs and understand caching

- [ ] Introduce shared configuration, pagination, and external-client dependencies using `Depends()` and `typing.Annotated`.
- [ ] Compose sub-dependencies and compare endpoint-level, router-level, and application-level dependencies.
- [ ] Demonstrate per-request dependency reuse by counting evaluations across a dependency graph.
- [ ] Reproduce diagnostic scenario 5 and demonstrate `Depends(..., use_cache=False)` when a fresh evaluation is required.
- [ ] Add a test using `app.dependency_overrides` and ensure overrides are cleared afterward.

**Deliverable:** Reusable dependency chains with tested caching and override behavior.

### T12 - Day 12: Manage application and request resource lifecycles

- [ ] Implement an async-context-manager `lifespan` to create the shared HTTP client and close it on shutdown.
- [ ] Expose shared resources through application state/dependencies rather than creating them inside every route.
- [ ] Build a `yield` dependency with cleanup in `finally`; test both successful and failing handlers.
- [ ] Explain the difference between process-wide resource ownership and request-scoped resource ownership.
- [ ] Ensure synchronous and asynchronous test fixtures execute startup and shutdown; explicitly manage lifespan around async HTTPX transport tests.

**Deliverable:** Tested startup, shutdown, and exception-safe request cleanup.

### T13 - Day 13: Add database models, migrations, and async sessions

- [ ] Configure PostgreSQL, an async driver, `create_async_engine()`, and `async_sessionmaker()` from environment settings.
- [ ] Create SQLAlchemy 2.0 models for users, inventory, orders, and order items with appropriate keys, relationships, constraints, and indexes.
- [ ] Initialize Alembic using an async-compatible setup; connect model metadata and create the initial migration.
- [ ] Verify migration upgrade and controlled downgrade against a disposable development database.
- [ ] Initialize/dispose database resources through lifespan; implement `get_db` with one session per request and exception-safe rollback/close.
- [ ] Configure `expire_on_commit=False` where appropriate and explain why it does not load previously unloaded relationships.
- [ ] Load relationships explicitly with `selectinload()` or `joinedload()`; reproduce and fix diagnostic scenario 2, `MissingGreenlet`.

**Deliverable:** A migrated database, isolated sessions, and response serialization that performs no unexpected lazy I/O.

### T14 - Day 14: Implement transactional inventory and order workflows

- [ ] Implement persistent inventory list/detail/create/update operations and the defined order creation/detail/status workflows.
- [ ] Separate endpoint handling from business operations and make transaction ownership explicit.
- [ ] Explain and demonstrate `flush()`, `commit()`, and `rollback()`; commit successful writes before returning success.
- [ ] Create the order, its lines, and stock deductions in one atomic transaction; verify an invalid line rolls back the entire operation.
- [ ] Prevent concurrent checkouts from overselling stock using a documented database locking or conditional-update strategy.
- [ ] Test ORM response serialization, missing items, insufficient stock, constraint failures, and successful database state transitions.
- [ ] Reproduce diagnostic scenario 3 in a controlled environment; verify request cleanup and explain connection pool limits across worker processes.

**Week 2 gate:** The API persists valid orders without overselling, rolls back failed work, releases resources, and demonstrates all concurrency/DI/database diagnostics introduced so far.

## Week 3: Security, operations, real-time behavior, and interview readiness

### T15 - Day 15: Implement login and token validation

- [ ] Select a maintained password-hashing approach; store hashes only and add a controlled local/test user provisioning path.
- [ ] Implement the password-form login exercise with `OAuth2PasswordRequestForm` and a token endpoint.
- [ ] Issue signed JWT access tokens with an identified subject, issuance time, and expiration.
- [ ] Use `OAuth2PasswordBearer` to extract bearer credentials, then explicitly validate JWT signatures, permitted algorithms, expiration, and required claims.
- [ ] Add settings for signing material and token lifetime; keep credentials and tokens out of logs.
- [ ] Test valid login, invalid credentials, missing/malformed tokens, expired tokens, and invalid signatures.

**Deliverable:** Login and independently verified bearer-token authentication.

### T16 - Day 16: Enforce authorization and configure CORS

- [ ] Build `get_current_user` and `get_current_active_user` dependency chains backed by persisted users.
- [ ] Implement the roles chosen in T01; restrict inventory administration and order status changes appropriately.
- [ ] Protect order creation and enforce ownership/role checks on order reads and tracking access.
- [ ] Distinguish unauthenticated 401 responses, including the relevant authentication header, from forbidden 403 responses.
- [ ] Configure explicit allowed CORS origins, methods, and headers; avoid wildcard origins with credentialed requests.
- [ ] Test role boundaries, inactive users, cross-user access, permitted preflight requests, and disallowed origins.

**Deliverable:** Protected resources with demonstrated authentication, authorization, and browser-origin behavior.

### T17 - Day 17: Add operational middleware and consistent exceptions

- [ ] Implement correlation IDs and request-duration logging with a consistent response header.
- [ ] Demonstrate middleware execution for matched routes, failures, 404s, and 405s; compare its scope with dependencies.
- [ ] Register handlers for domain exceptions, `StarletteHTTPException`, and FastAPI's `RequestValidationError`.
- [ ] Preserve intentional status codes and authentication headers while standardizing error payloads.
- [ ] Test validation errors, domain conflicts, unexpected failures, and error-response correlation IDs.
- [ ] Explain when middleware, dependencies, or service-layer logic is the appropriate abstraction.

**Deliverable:** Observable request handling and a consistent, tested error contract.

### T18 - Day 18: Add post-commit notifications and study reliability

- [ ] Schedule a lightweight, best-effort order notification with `BackgroundTasks` only after the checkout transaction commits.
- [ ] Pass identifiers or immutable data into tasks; create a separate session if a task needs database access.
- [ ] Verify that rolled-back checkouts schedule no success notification and task failure does not undo a committed order.
- [ ] Reproduce or demonstrate diagnostic scenario 4: pending in-process tasks can be lost when the worker terminates.
- [ ] Explain task frameworks/workers versus brokers, and document when durable delivery, retries, idempotency, or a transactional outbox would be required.
- [ ] Document that the best-effort notification has no durability guarantee; keep stock/order correctness inside the committed workflow.

**Deliverable:** A post-commit notification path and a clear explanation of its reliability limits.

### T19 - Day 19: Implement authorized real-time order tracking

- [ ] Choose WebSockets or SSE and document the choice, client authentication approach, and expected message format.
- [ ] Implement an authenticated order-status feed with ownership/role checks.
- [ ] Publish only committed order status transitions; avoid holding a request database session for the lifetime of a connection.
- [ ] Handle disconnects, cancellation, cleanup, and relevant heartbeat/reconnect behavior.
- [ ] Test status delivery, forbidden subscriptions, and disconnect cleanup.
- [ ] Document whether events are live-only or replayable; explain how an in-memory broadcaster is limited across multiple workers.
- [ ] Document the connection/authentication protocol and provide a runnable client example; retain SSE versus WebSocket trade-off knowledge whichever is selected.

**Deliverable:** One functioning and documented real-time tracking mechanism.

### T20 - Day 20: Complete integration tests and verify the API documentation

- [ ] Consolidate async pytest fixtures using `httpx.AsyncClient` with `ASGITransport`, explicit lifespan handling, and compatible async test configuration.
- [ ] Override database/external-service dependencies; isolate test data, clean up resources, and reset overrides.
- [ ] Cover successful and rejected schemas, response filtering, login/RBAC, ownership, inventory behavior, order transitions, rollback, and notifications.
- [ ] Run concurrent checkout tests against PostgreSQL; do not use SQLite results as proof of PostgreSQL locking correctness.
- [ ] Cover lifecycle cleanup, dependency caching, middleware/error headers, upstream failures, and the chosen tracking protocol.
- [ ] Review `/openapi.json`, `/docs`, and `/redoc` against the actual HTTP API, including bearer security, schemas, examples, and error codes.
- [ ] Run the full suite from a clean test database and record reproducible commands and results.

**Deliverable:** A repeatable, isolated test suite and documentation that matches implemented behavior.

### T21 - Day 21: Review deployment, diagnostics, and interview delivery

- [ ] Write local startup, migration, test, and demo instructions, including environment prerequisites and test-user setup.
- [ ] Verify current, platform-appropriate production serving guidance; explain Uvicorn workers, process supervision, and the platform/version constraints of optional event loops or Gunicorn integrations.
- [ ] Explain how worker count affects shared state, database connection budgets, background tasks, and real-time delivery.
- [ ] Rehearse all five diagnostic scenarios: symptom, root cause, reproduction, correction, verification, and trade-off.
- [ ] Prepare short explanations for all 11 topics using context -> mechanism -> trade-off.
- [ ] Run a capstone demonstration: login, inventory lookup, successful checkout, rejected checkout with rollback, access denial, post-commit notification, and live status tracking.
- [ ] Review the candidate evaluation rubric and resolve remaining gaps in concurrency, session management, authorization, or reliability explanations.

**Week 3 gate:** All seven capstone features work, their failure paths are tested, and the project can be demonstrated and explained from a clean setup.

## Coverage map

| FASTAPI.md topic | Primary tasks |
| --- | --- |
| 1. Architectural foundations and runtime standards | T02, T08, T21 |
| 2. Concurrency mechanics | T08-T10 |
| 3. Routing, parameter binding, and request lifecycle | T02-T04 |
| 4. Pydantic validation, schemas, and serialization | T05-T07, T13 |
| 5. Dependency injection and lifecycle management | T11-T12, T16 |
| 6. Async database integration and migrations | T13-T14 |
| 7. Error handling and HTTP responses | T04, T17 |
| 8. Security and authentication | T15-T16 |
| 9. Middleware versus dependencies | T11, T17 |
| 10. Background tasks and real-time streaming | T18-T19 |
| 11. OpenAPI and testing | T02, T07, T20 |

| Diagnostic scenario from FASTAPI_STUDY_PLAN.md | Reproduce and resolve | Final rehearsal |
| --- | --- | --- |
| 1. Event-loop starvation | T09 | T21 |
| 2. MissingGreenlet | T13 | T21 |
| 3. Connection pool exhaustion | T14 | T21 |
| 4. Lost in-process background tasks | T18 | T21 |
| 5. Unintended dependency memoization | T11 | T21 |

## Final acceptance checklist

- [ ] Lifespan manages the shared HTTP client and database engine.
- [ ] Separate input/output schemas enforce validation and prevent private-field leakage.
- [ ] Request-scoped database dependencies clean up on success/failure, with explicit transaction boundaries.
- [ ] Active-user authentication and role/ownership authorization protect order workflows.
- [ ] Successful checkout commits before scheduling a lightweight background notification.
- [ ] Authenticated WebSocket or SSE tracking publishes committed order state changes.
- [ ] Async integration tests verify schema rejection, permissions, persistence, and state transitions using dependency overrides.
- [ ] All 11 interview topics and all five diagnostic scenarios can be demonstrated and explained.

## Optional extensions after the required capstone

- [ ] Implement a durable queue, worker, retry policy, and idempotent notification consumer; address the database/message publishing gap.
- [ ] Add a shared event transport for multi-worker order tracking and document its delivery semantics.
- [ ] Add the second real-time transport and compare its operational behavior.
- [ ] Add CI and a reproducible deployment package after the local setup and test suite are stable.

