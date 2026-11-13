"""Authentication services with a replaceable credential verification boundary."""

from __future__ import annotations

import hmac
from typing import Protocol

from app.schemas.auth import LoginInput, UserRead

_DEMO_USERNAME = "admin"
_DEMO_PASSWORD = "password"
_DEMO_USER = UserRead(id=1, username=_DEMO_USERNAME, role="admin")


class CredentialVerifier(Protocol):
    """Interface for swapping demo credentials for persisted users later."""

    def authenticate(self, credentials: LoginInput) -> UserRead | None:
        """Return the public user on success, otherwise None."""
        ...


class StaticCredentialVerifier:
    """Local learning verifier for the agreed static admin/password account."""

    def authenticate(self, credentials: LoginInput) -> UserRead | None:
        """Check demo credentials; production auth will use a different provider."""
        username_ok = hmac.compare_digest(
            credentials.username.encode(), _DEMO_USERNAME.encode()
        )
        password_ok = hmac.compare_digest(
            credentials.password.encode(), _DEMO_PASSWORD.encode()
        )
        return _DEMO_USER if username_ok and password_ok else None
