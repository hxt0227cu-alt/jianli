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


@dataclass(frozen=True, slots=True)
class Principal:
    id: UUID
    email: str
    role: UserRole
    verified: bool
