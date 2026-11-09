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
