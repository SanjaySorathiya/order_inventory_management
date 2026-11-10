"""Isolated T04 inputs and HTTP errors; run separately from the capstone API."""

import codecs
from typing import Annotated

from fastapi import (
    Cookie,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field

from app.api.errors import validation_error_response

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024

app = FastAPI(
    title="T04 request-format exercises",
    description="Isolated learning examples. Uploads are inspected, never retained.",
)
app.add_exception_handler(RequestValidationError, validation_error_response)


class Message(BaseModel):
    """The JSON counterpart to the form field below."""

    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=120)


@app.get("/headers-cookies")
async def headers_cookies(
    x_request_id: Annotated[str | None, Header(min_length=1, max_length=64)] = None,
    x_demo_tag: Annotated[
        str | None, Header(convert_underscores=False, min_length=1, max_length=64)
    ] = None,
    theme: Annotated[str | None, Cookie(min_length=1, max_length=20)] = None,
) -> dict[str, str | None]:
    """Bind X-Request-ID, literal x_demo_tag, and a non-authentication cookie."""
    return {"x_request_id": x_request_id, "x_demo_tag": x_demo_tag, "theme": theme}


@app.post("/json")
async def json_message(body: Message) -> dict[str, str]:
    """Read an application/json body; form encoding is a separate contract."""
    return {"message": body.message}


@app.post("/form")
async def form_message(
    message: Annotated[str, Form(min_length=1, max_length=120)],
) -> dict[str, str]:
    """Read a form field (URL-encoded or multipart), without creating a resource."""
    return {"message": message}


def upload_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code, detail={"code": code, "message": message})


async def inspect_text_upload(upload: UploadFile) -> tuple[str, int, int]:
    """Count bounded UTF-8 text incrementally and always close the temporary file."""
    try:
        filename = (upload.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        media_type = (upload.content_type or "").split(";", 1)[0].strip().lower()
        if not filename.lower().endswith(".txt") or media_type != "text/plain":
            raise upload_error(
                415, "unsupported_file_type", "Upload a .txt file with type text/plain."
            )

        decoder = codecs.getincrementaldecoder("utf-8")()
        size_bytes = 0
        character_count = 0
        while chunk := await upload.read(READ_CHUNK_BYTES):
            size_bytes += len(chunk)
            if size_bytes > MAX_UPLOAD_BYTES:
                raise upload_error(
                    413, "file_too_large", "File must be at most 2 MiB (2097152 bytes)."
                )
            text = decoder.decode(chunk)
            if any(ord(char) < 32 and char not in "\t\n\r" for char in text):
                raise upload_error(
                    422,
                    "invalid_text",
                    "File must contain UTF-8 text without binary controls.",
                )
            character_count += len(text)
        character_count += len(decoder.decode(b"", final=True))
        if size_bytes == 0:
            raise upload_error(422, "empty_file", "File must not be empty.")
        return filename, size_bytes, character_count
    except UnicodeDecodeError:
        raise upload_error(
            422, "invalid_text", "File must contain valid UTF-8 text."
        ) from None
    finally:
        await upload.close()


@app.post(
    "/upload",
    responses={
        413: {"description": "File exceeds the 2 MiB processing limit."},
        415: {"description": "Filename or declared file media type is unsupported."},
        422: {
            "description": "Missing/repeated fields, empty file, or invalid UTF-8 text."
        },
    },
)
async def upload_text(
    request: Request,
    file: Annotated[
        UploadFile, File(description="One nonempty UTF-8 .txt file, <= 2 MiB.")
    ],
    label: Annotated[str, Form(min_length=1, max_length=80)],
) -> dict[str, str | int]:
    """Inspect one file plus a label; no file or text content is retained."""
    # FastAPI already parsed the form. Reuse it to reject silently selected duplicates.
    form = await request.form()
    try:
        if (
            len(form.getlist("file")) != 1
            or len(form.getlist("label")) != 1
            or set(form) != {"file", "label"}
        ):
            raise upload_error(
                422, "invalid_upload_fields", "Provide exactly one file and one label."
            )
        filename, size_bytes, character_count = await inspect_text_upload(file)
        return {
            "filename": filename,
            "content_type": "text/plain",
            "size_bytes": size_bytes,
            "character_count": character_count,
            "label": label,
        }
    finally:
        # Also close any extra files rejected before inspection.
        await form.close()


@app.get(
    "/errors/rate-limited",
    status_code=429,
    responses={
        429: {
            "description": "Unconditional HTTPException demonstration, not a rate limiter.",
            "headers": {
                "Retry-After": {
                    "description": "Seconds before retrying.",
                    "schema": {"type": "integer", "example": 60},
                }
            },
        }
    },
)
async def rate_limited() -> None:
    """Demonstrate an expected failure with structured detail and an optional header."""
    raise HTTPException(
        status_code=429,
        detail={"code": "rate_limited", "message": "Try again later."},
        headers={"Retry-After": "60"},
    )
