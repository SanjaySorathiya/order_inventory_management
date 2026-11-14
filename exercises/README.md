# Isolated learning exercises

Keep request-format experiments, concurrency demonstrations, and intentionally
broken diagnostic examples here as their checklist tasks are introduced.
Run exercises explicitly; the capstone application does not import them.
The main API entry point is app.main:app.

## T03: Parameter binding and route ordering

Inventory CRUD runs in the main API. The separate t03_parameters.py app
demonstrates required versus optional/nullable queries and static routes
registered before dynamic routes.

~~~sh
uv run --locked uvicorn exercises.t03_parameters:app --port 8001 --reload
~~~

Open http://127.0.0.1:8001/docs or try:

- /parameters?required=hello&required_nullable=world returns 200 with optional_nullable set to null.
- Omitting required or required_nullable returns 422.
- Adding optional_nullable=null supplies the string "null"; an HTTP query has no JSON null value.
- /items/search reaches the static route; /items/7 binds a positive integer ID.
- /items/0 and /items/abc return 422.

Tests also construct an intentionally misordered app: a dynamic route
registered first captures /items/search and produces 422 during integer
validation. That broken route order is confined to the test.

~~~sh
uv run --locked python -m pytest tests/test_t03_parameters.py -q
~~~

See [T03 notes](../docs/T03_D3.md) for explanations and main API examples.

## T04: Special inputs, uploads, and HTTP errors

~~~sh
uv run --locked uvicorn exercises.t04_requests:app --host 127.0.0.1 --port 8002 --reload
~~~

Open http://127.0.0.1:8002/docs.

| Route | Demonstration |
| --- | --- |
| GET /headers-cookies | Header underscore/hyphen conversion, case-insensitivity, and Cookie() binding. |
| POST /json | Required message in a JSON document. |
| POST /form | Required message in a URL-encoded or multipart text field. |
| POST /upload | Exactly one file and label, temporary text inspection. |
| GET /errors/rate-limited | HTTPException 429, structured detail, and Retry-After: 60. |

Upload one nonempty UTF-8 .txt file with declared type text/plain, at most
2 MiB (2,097,152 bytes), and a label of 1-80 characters. Wrong type returns 415,
oversize returns 413, and missing/repeated fields or invalid text return 422.
Files are closed on success and rejection, including disk-spooled uploads;
nothing is retained. The handler's byte limit applies after multipart parsing.

The 429 route is an unconditional error demonstration. The main API continues
to demonstrate creation (201 with Location), deletion (empty 204), missing
inventory (404), and duplicate SKU conflicts (409).

~~~sh
uv run --locked python -m pytest tests/test_t04_requests.py tests/test_http_contract.py -q
~~~

See [T04 notes](../docs/T04_D4.md) for the HTTP contract, spooling/cleanup
explanation, runnable PowerShell and Bash/zsh examples, and verification.

## T07: Response filtering and invalid server responses

~~~sh
uv run --locked uvicorn exercises.t07_response_filtering:app --port 8003 --reload
~~~

Open http://127.0.0.1:8003/docs.

| Route | Demonstration |
| --- | --- |
| GET /t07/users/{user_id} | Internal record filtered through the public UserRead schema; password_hash, is_active, and support_note are absent. |
| GET /t07/orders/{order_id} | Nested OrderRead filtering; line cost_minor and order fraud_score are absent. |
| POST /t07/users/validate | Invalid body returns 422 (client error); valid body returns 200. |
| GET /t07/users-leaky | Intentionally broken: returns a dict with password_hash. The forbidden extra key causes a 500 (server error). |
| GET /t07/users-incomplete | Intentionally broken: omits a required field and returns a 500. |

The two broken routes exist only to show invalid server responses. Use the
`/t07/users/validate` route to compare them with a client error.

~~~sh
uv run --locked python -m pytest tests/test_t07_response_filtering.py tests/test_t07_contract.py -q
~~~

See [T07 notes](../docs/T07_D7.md) for the filtering mechanics, the OpenAPI
contract review, and the Week 1 gate.
