"""Stable authentication errors matching the approved problem envelope."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuthError(Exception):
    code: str
    status: int
    title: str
    detail: str
    retry_after_seconds: int | None = None
