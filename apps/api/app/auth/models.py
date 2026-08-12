"""Authentication request and principal models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

UserRole = Literal["interviewer", "owner_admin"]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320, json_schema_extra={"format": "email"})
    password: str = Field(min_length=1, max_length=72)
    remember_me: bool

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if (
            not separator
            or not local
            or "." not in domain
            or any(char.isspace() for char in normalized)
        ):
            raise ValueError("invalid email")
        return normalized

    @field_validator("password")
    @classmethod
    def reject_overlong_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds 72 UTF-8 bytes")
        return value


class UserSummary(BaseModel):
    id: UUID
    email: str
    role: UserRole
    verified: bool


class RegisterRequest(BaseModel):
    """Public self-service registration (creates an unverified interviewer).

    Schema mirrors ``docs/api/openapi.yaml`` ``RegisterRequest``: BCrypt password is
    10-72 UTF-8 bytes (enforced here and again by ``PasswordHasher``).
    """

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320, json_schema_extra={"format": "email"})
    password: str = Field(min_length=10, max_length=72)

    # Mirrors LoginRequest normalization so a registered email matches a login email.
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if (
            not separator
            or not local
            or "." not in domain
            or any(char.isspace() for char in normalized)
        ):
            raise ValueError("invalid email")
        return normalized

    @field_validator("password")
    @classmethod
    def reject_overlong_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds 72 UTF-8 bytes")
        return value


class TokenRequest(BaseModel):
    """Opaque one-time token (verification or reset link); stored only as its SHA-256 hash.

    Mirrors ``docs/api/openapi.yaml`` ``TokenRequest``: only ``minLength: 32`` is
    declared (no upper bound), so we do not cap length here and avoid a 422 the
    contract does not define.
    """

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32)


class EmailRequest(BaseModel):
    """Email address only (resend / reset request)."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320, json_schema_extra={"format": "email"})

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if (
            not separator
            or not local
            or "." not in domain
            or any(char.isspace() for char in normalized)
        ):
            raise ValueError("invalid email")
        return normalized


class ResetPasswordRequest(BaseModel):
    """Consume a password reset link and set a new BCrypt password (``confirmPasswordReset``)."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32)
    new_password: str = Field(min_length=10, max_length=72)

    @field_validator("new_password")
    @classmethod
    def reject_overlong_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds 72 UTF-8 bytes")
        return value


@dataclass(frozen=True, slots=True)
class Principal:
    id: UUID
    email: str
    role: UserRole
    verified: bool
