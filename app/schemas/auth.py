"""Login input and public user output schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from app.schemas.inventory import PositiveId


def _normalize_username(value: object) -> object:
    """Apply the account contract's trim/lowercase normalization before checks."""
    if isinstance(value, str):
        return value.strip().lower()
    return value


Username = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9_.-]{2,63}$",
    ),
    BeforeValidator(_normalize_username),
]
Password = Annotated[str, Field(min_length=1)]


class LoginInput(BaseModel):
    """OAuth password-form fields; password whitespace is preserved verbatim."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    password: Password
    grant_type: Literal["password"]
    scope: Literal[""] = ""


class UserRead(BaseModel):
    """Public user representation; private credentials and account flags are omitted."""

    model_config = ConfigDict(extra="forbid", frozen=True, from_attributes=True)

    id: PositiveId
    username: Username
    role: Literal["customer", "admin"]
