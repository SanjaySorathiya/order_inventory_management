"""Versioned auth route; real credentials and token issuance arrive in T15."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", status_code=501)
def issue_token() -> None:
    """Pending T15: form validation, password hashes, and signed access tokens."""
    raise HTTPException(
        status_code=501,
        detail={
            "code": "authentication_not_implemented",
            "message": "Token authentication will be implemented in T15.",
        },
    )
