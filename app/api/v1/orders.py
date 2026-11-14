"""Order route registration and path binding; workflows arrive in T14-T19."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.schemas.inventory import MAX_INT64

router = APIRouter(prefix="/orders", tags=["Orders"])
OrderId = Annotated[int, Path(gt=0, le=MAX_INT64)]

NOT_IMPLEMENTED = {
    "description": (
        "Order workflows are not implemented yet. The contract response (for example "
        "201 or 200 with OrderRead) is added with persistence and authentication."
    ),
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "code": "orders_not_implemented",
                    "message": "Order workflows require the later persistence and auth tasks.",
                }
            }
        }
    },
}


def _pending() -> None:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "orders_not_implemented",
            "message": "Order workflows require the later persistence and auth tasks.",
        },
    )


@router.post(
    "",
    status_code=501,
    summary="Create an order (pending)",
    description="Checkout arrives in T14. Currently returns 501 with a structured detail.",
    responses={501: NOT_IMPLEMENTED},
)
def create_order() -> None:
    _pending()


@router.get(
    "/{order_id}",
    status_code=501,
    summary="Get an order (pending)",
    description="Owner/admin order reads arrive in T16. Currently returns 501.",
    responses={501: NOT_IMPLEMENTED},
)
def read_order(order_id: OrderId) -> None:
    _pending()


@router.patch(
    "/{order_id}/status",
    status_code=501,
    summary="Change order status (pending)",
    description="Admin status transitions arrive in T14/T16. Currently returns 501.",
    responses={501: NOT_IMPLEMENTED},
)
def change_order_status(order_id: OrderId) -> None:
    _pending()


@router.get(
    "/{order_id}/events",
    status_code=501,
    summary="Track order status (pending)",
    description="Real-time order tracking arrives in T19. Currently returns 501.",
    responses={501: NOT_IMPLEMENTED},
)
def track_order(order_id: OrderId) -> None:
    _pending()
