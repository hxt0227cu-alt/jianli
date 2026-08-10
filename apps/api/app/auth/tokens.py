"""Opaque session and CSRF token primitives."""

from __future__ import annotations

import hashlib
import hmac
import secrets


class SessionTokens:
    def __init__(self, csrf_hmac_key: str) -> None:
        key = csrf_hmac_key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("CSRF HMAC key must be at least 32 UTF-8 bytes")
        self._csrf_key = key

    @staticmethod
    def generate() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode("ascii")).hexdigest()

    def csrf(self, session_token: str) -> str:
        return hmac.new(self._csrf_key, session_token.encode("ascii"), hashlib.sha256).hexdigest()

    def valid_csrf(self, session_token: str, cookie: str | None, header: str | None) -> bool:
        if not cookie or not header:
            return False
        expected = self.csrf(session_token)
        return hmac.compare_digest(cookie, expected) and hmac.compare_digest(header, expected)
