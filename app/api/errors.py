"""Minimal validation error rendering without echoing request values."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_error_response(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Keep actionable locations/types/messages while excluding submitted values."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {key: error[key] for key in ("loc", "msg", "type")}
                for error in exc.errors()
            ]
        },
    )
