"""T03 parameter-binding and route-ordering exercises, separate from the API."""

from typing import Annotated

from fastapi import FastAPI, Path, Query

app = FastAPI(title="T03 parameter exercises")


@app.get("/parameters")
async def parameters(
    required: Annotated[str, Query(min_length=1)],
    required_nullable: Annotated[str | None, Query()],
    optional_nullable: Annotated[str | None, Query()] = None,
) -> dict[str, str | None]:
    """Nullable annotations do not make a parameter optional."""
    return {
        "required": required,
        "required_nullable": required_nullable,
        "optional_nullable": optional_nullable,
    }


# Register a static route before a dynamic route matching the same prefix.
@app.get("/items/search")
async def search_items() -> dict[str, str]:
    return {"route": "search"}


@app.get("/items/{item_id}")
async def read_item(item_id: Annotated[int, Path(gt=0)]) -> dict[str, int]:
    return {"item_id": item_id}
