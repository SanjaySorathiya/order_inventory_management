"""Request binding, upload boundaries, real spooling, and cleanup for T04."""

import asyncio
from contextlib import ExitStack
from tempfile import SpooledTemporaryFile

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette import formparsers
from starlette.datastructures import Headers

from exercises.t04_requests import (
    MAX_UPLOAD_BYTES,
    READ_CHUNK_BYTES,
    app,
    inspect_text_upload,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def spooled_files(monkeypatch):
    """Capture genuine parser-owned files without forcing rollover via fileno()."""
    captured = []
    with ExitStack() as stack:

        def capture(*args, **kwargs):
            temporary = stack.enter_context(SpooledTemporaryFile(*args, **kwargs))
            captured.append(temporary)
            return temporary

        monkeypatch.setattr(formparsers, "SpooledTemporaryFile", capture)
        yield captured


def send_file(
    client, content=b"Hello\n", filename="notes.txt", media_type="text/plain"
):
    return client.post(
        "/upload",
        data={"label": "demo"},
        files={"file": (filename, content, media_type)},
    )


def assert_error(response, status_code, code):
    assert response.status_code == status_code
    assert response.json()["detail"]["code"] == code
    assert isinstance(response.json()["detail"]["message"], str)


def test_headers_convert_underscores_and_cookies_keep_their_binding(client):
    response = client.get(
        "/headers-cookies",
        headers={
            "X-ReQuEsT-ID": "demo-id",
            "x_demo_tag": "literal-underscore",
            "Cookie": "theme=dark",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "x_request_id": "demo-id",
        "x_demo_tag": "literal-underscore",
        "theme": "dark",
    }
    response = client.get(
        "/headers-cookies",
        headers={"x_request_id": "ignored", "x-demo-tag": "ignored"},
        params={"theme": "ignored"},
    )
    assert response.json() == {"x_request_id": None, "x_demo_tag": None, "theme": None}


@pytest.mark.parametrize(
    ("headers", "location"),
    [
        ({"X-Request-ID": "x" * 65}, ["header", "x-request-id"]),
        ({"Cookie": "theme=" + "x" * 21}, ["cookie", "theme"]),
    ],
)
def test_header_and_cookie_constraints(client, headers, location):
    response = client.get("/headers-cookies", headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == location


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        ("/json", {"json": {"message": "hello"}}),
        ("/form", {"data": {"message": "hello"}}),
        ("/form", {"files": {"message": (None, "hello")}}),
    ],
)
def test_json_urlencoded_and_multipart_form_inputs(client, path, kwargs):
    response = client.post(path, **kwargs)
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        ("/json", {"data": {"message": "hello"}}),
        ("/json", {"json": {}}),
        ("/json", {"json": {"message": "hello", "extra": "secret"}}),
        ("/form", {"json": {"message": "secret"}}),
        ("/form", {"data": {}}),
        ("/form", {"data": {"message": "x" * 121}}),
        ("/upload", {"json": {"file": "secret", "label": "demo"}}),
        ("/upload", {"data": {"file": "text", "label": "demo"}}),
    ],
)
def test_wrong_formats_missing_fields_and_constraints(client, path, kwargs):
    response = client.post(path, **kwargs)
    assert response.status_code == 422
    assert "secret" not in response.text
    assert all(
        set(error) == {"loc", "msg", "type"} for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    ("content", "character_count"),
    [
        (b"Hello\n", 6),
        ("Hello \u20b9\n".encode(), 8),
        (b"a" * MAX_UPLOAD_BYTES, MAX_UPLOAD_BYTES),
        (b"a" * (READ_CHUNK_BYTES - 1) + "\u20b9".encode(), READ_CHUNK_BYTES),
    ],
)
def test_valid_upload_counts_utf8_and_closes_temporary_files(
    client, spooled_files, content, character_count
):
    response = send_file(client, content)
    assert response.status_code == 200
    assert response.json() == {
        "filename": "notes.txt",
        "content_type": "text/plain",
        "size_bytes": len(content),
        "character_count": character_count,
        "label": "demo",
    }
    assert len(spooled_files) == 1
    assert spooled_files[0].closed
    # This is an observation of the installed parser, not an application size limit.
    assert spooled_files[0]._rolled is (
        len(content) > formparsers.MultiPartParser.spool_max_size
    )


@pytest.mark.parametrize(
    ("content", "filename", "media_type", "status_code", "code"),
    [
        (
            b"a" * (MAX_UPLOAD_BYTES + 1),
            "large.txt",
            "text/plain",
            413,
            "file_too_large",
        ),
        (b"text", "notes.pdf", "text/plain", 415, "unsupported_file_type"),
        (b"text", "notes.txt", "application/pdf", 415, "unsupported_file_type"),
        (b"", "empty.txt", "text/plain", 422, "empty_file"),
        (b"\xff", "notes.txt", "text/plain", 422, "invalid_text"),
        (b"\xe2\x82", "notes.txt", "text/plain", 422, "invalid_text"),
        (b"binary\x00text", "notes.txt", "text/plain", 422, "invalid_text"),
    ],
)
def test_rejected_uploads_close_temporary_files(
    client, spooled_files, content, filename, media_type, status_code, code
):
    response = send_file(client, content, filename, media_type)
    assert_error(response, status_code, code)
    assert len(spooled_files) == 1
    assert spooled_files[0].closed


@pytest.mark.parametrize(
    "files",
    [
        [
            ("file", ("one.txt", b"one", "text/plain")),
            ("file", ("two.txt", b"two", "text/plain")),
        ],
        [
            ("file", ("one.txt", b"one", "text/plain")),
            ("other", ("two.txt", b"two", "text/plain")),
        ],
        [
            ("file", ("one.txt", b"one", "text/plain")),
            ("label", (None, "second label")),
        ],
    ],
)
def test_duplicate_or_extra_upload_parts_are_rejected_and_all_closed(
    client, spooled_files, files
):
    response = client.post("/upload", data={"label": "demo"}, files=files)
    assert_error(response, 422, "invalid_upload_fields")
    assert spooled_files
    assert all(temporary.closed for temporary in spooled_files)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"files": {"file": ("notes.txt", b"text", "text/plain")}},
        {
            "data": {"label": "demo"},
            "files": {"wrong_name": ("notes.txt", b"text", "text/plain")},
        },
        {
            "data": {"label": "x" * 81},
            "files": {"file": ("notes.txt", b"text", "text/plain")},
        },
    ],
)
def test_framework_closes_files_when_validation_fails_before_handler(
    client, spooled_files, kwargs
):
    response = client.post("/upload", **kwargs)
    assert response.status_code == 422
    assert spooled_files
    assert all(temporary.closed for temporary in spooled_files)


def test_inspection_closes_file_on_unexpected_read_failure(monkeypatch):
    with SpooledTemporaryFile(max_size=1024) as temporary:
        upload = UploadFile(
            file=temporary,
            filename="notes.txt",
            headers=Headers({"content-type": "text/plain"}),
        )

        async def failing_read(_size):
            raise OSError("exercise read failure")

        monkeypatch.setattr(upload, "read", failing_read)
        with pytest.raises(OSError, match="exercise read failure"):
            asyncio.run(inspect_text_upload(upload))
        # Assert before the context manager exits, so it cannot mask failed cleanup.
        assert temporary.closed


def test_http_exception_keeps_status_detail_and_optional_headers(client):
    response = client.get("/errors/rate-limited")
    assert_error(response, 429, "rate_limited")
    assert response.json()["detail"]["message"] == "Try again later."
    assert response.headers["retry-after"] == "60"


def test_openapi_describes_parameter_sources_payloads_and_error_headers(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    parameters = {
        (parameter["in"], parameter["name"])
        for parameter in paths["/headers-cookies"]["get"]["parameters"]
    }
    assert parameters == {
        ("header", "x-request-id"),
        ("header", "x_demo_tag"),
        ("cookie", "theme"),
    }
    for path, media_type in [
        ("/json", "application/json"),
        ("/form", "application/x-www-form-urlencoded"),
        ("/upload", "multipart/form-data"),
    ]:
        assert media_type in paths[path]["post"]["requestBody"]["content"]
    assert {"200", "413", "415", "422"} <= paths["/upload"]["post"]["responses"].keys()
    assert (
        "Retry-After"
        in paths["/errors/rate-limited"]["get"]["responses"]["429"]["headers"]
    )
