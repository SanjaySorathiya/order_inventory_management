"""Versioned auth route; real credentials and token issuance arrive in T15."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/token",
    status_code=501,
    summary="Issue an access token (pending)",
    description=(
        "Pending T15: password-form login and signed bearer tokens. The contract "
        "success response (200 TokenRead) is not yet implemented."
    ),
    responses={
        501: {
            "description": "Token authentication is not implemented yet.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "authentication_not_implemented",
                            "message": "Token authentication will be implemented in T15.",
                        }
                    }
                }
            },
        }
    },
)
def issue_token() -> None:
    """Pending T15: form validation, password hashes, and signed access tokens."""
    raise HTTPException(
        status_code=501,
        detail={
            "code": "authentication_not_implemented",
            "message": "Token authentication will be implemented in T15.",
        },
    )
