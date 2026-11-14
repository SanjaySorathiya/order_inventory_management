"""T07 OpenAPI review: documented routes, status codes, and metadata against the T01 contract."""

import pytest

from app.core.config import Settings
from app.main import create_app

HTTP_METHODS = ("get", "post", "put", "patch", "delete")

# Status codes the T01 contract requires for each route. Routes still returning
# 501 document only the status they implement today; contract successes are
# added with their owning task (see docs/T07_D7.md, "Contract gaps").
EXPECTED_RESPONSES = {
    ("/health", "get"): {"200"},
    ("/api/v1/auth/token", "post"): {"501"},
    ("/api/v1/inventory", "get"): {"200", "403", "422"},
    ("/api/v1/inventory", "post"): {"201", "409", "422", "501"},
    ("/api/v1/inventory/{item_id}", "get"): {"200", "404", "422"},
    ("/api/v1/inventory/{item_id}", "put"): {"200", "404", "422", "501"},
    ("/api/v1/inventory/{item_id}", "patch"): {"200", "404", "422", "501"},
    ("/api/v1/inventory/{item_id}", "delete"): {"204", "404", "422", "501"},
    ("/api/v1/orders", "post"): {"501"},
    ("/api/v1/orders/{order_id}", "get"): {"501"},
    ("/api/v1/orders/{order_id}/status", "patch"): {"501"},
    ("/api/v1/orders/{order_id}/events", "get"): {"501"},
}


@pytest.fixture(scope="module")
def spec() -> dict:
    return create_app(Settings(_env_file=None, environment="test")).openapi()


def test_documented_routes_match_the_contract_paths(spec) -> None:
    documented = {
        (path, method)
        for path, operations in spec["paths"].items()
        for method in operations
        if method in HTTP_METHODS
    }

    assert set(EXPECTED_RESPONSES) == documented


@pytest.mark.parametrize(("path", "method"), sorted(EXPECTED_RESPONSES))
def test_each_operation_documents_the_expected_status_codes(spec, path, method) -> None:
    responses = spec["paths"][path][method]["responses"]

    assert EXPECTED_RESPONSES[(path, method)] <= set(responses)


@pytest.mark.parametrize(("path", "method"), sorted(EXPECTED_RESPONSES))
def test_each_operation_has_summary_description_and_tags(spec, path, method) -> None:
    operation = spec["paths"][path][method]

    assert operation.get("summary", "").strip()
    assert operation.get("description", "").strip()
    assert operation.get("tags")


def test_success_responses_reference_the_public_schemas(spec) -> None:
    paths = spec["paths"]

    def schema_ref(path: str, method: str, status: str) -> str:
        content = paths[path][method]["responses"][status]["content"]
        return content["application/json"]["schema"]["$ref"]

    assert schema_ref("/api/v1/inventory", "get", "200").endswith("/InventoryPage")
    assert schema_ref("/api/v1/inventory/{item_id}", "get", "200").endswith(
        "/InventoryRead"
    )
    assert schema_ref("/api/v1/inventory", "post", "201").endswith("/InventoryRead")


def test_published_inventory_schemas_expose_no_private_fields(spec) -> None:
    """UserRead is not on a capstone route yet; its filtering is tested in the exercise."""
    schemas = spec["components"]["schemas"]

    assert set(schemas["InventoryRead"]["properties"]) == {
        "id",
        "sku",
        "name",
        "description",
        "unit_price_minor",
        "stock",
        "is_active",
        "currency",
        "created_at",
        "updated_at",
    }
    assert "UserRead" not in schemas


def test_schema_examples_are_published(spec) -> None:
    schemas = spec["components"]["schemas"]

    for name in ("InventoryCreate", "InventoryRead", "InventoryPage", "InventoryPatch"):
        assert schemas[name].get("examples"), name


def test_known_contract_gaps_are_not_claimed_as_implemented(spec) -> None:
    """Planned contract items must stay absent until their owning task implements them."""
    paths = spec["paths"]

    assert "/health/ready" not in paths
    assert "200" not in paths["/api/v1/auth/token"]["post"]["responses"]
    assert "200" not in paths["/api/v1/orders"]["post"]["responses"]
