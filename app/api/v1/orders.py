"""Order route registration and path binding; workflows arrive in T14-T19."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.schemas.inventory import MAX_INT64

router = APIRouter(prefix="/orders", tags=["Orders"])
OrderId = Annotated[int, Path(gt=0, le=MAX_INT64)]


def _pending() -> None:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "orders_not_implemented",
            "message": "Order workflows require the later persistence and auth tasks.",
        },
    )


@router.post("", status_code=501)
def create_order() -> None:
    _pending()


@router.get("/{order_id}", status_code=501)
def read_order(order_id: OrderId) -> None:
    _pending()


@router.patch("/{order_id}/status", status_code=501)
def change_order_status(order_id: OrderId) -> None:
    _pending()


@router.get("/{order_id}/events", status_code=501)
def track_order(order_id: OrderId) -> None:
    _pending()
