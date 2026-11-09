"""Compose the versioned business routers."""

from fastapi import APIRouter

from app.api.v1 import auth, inventory, orders

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(inventory.router)
router.include_router(orders.router)
