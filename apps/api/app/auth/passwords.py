"""BCrypt password policy with explicit UTF-8 byte boundaries."""

from __future__ import annotations

import bcrypt

BCRYPT_COST = 12
MIN_PASSWORD_BYTES = 10
MAX_PASSWORD_BYTES = 72


class PasswordPolicyError(ValueError):
    """Raised when a password violates the approved byte policy."""


class PasswordHasher:
    def __init__(self) -> None:
        self._dummy_hash = bcrypt.hashpw(b"jianli-dummy-password", bcrypt.gensalt(BCRYPT_COST))

    @staticmethod
    def _bytes(password: str, *, require_minimum: bool) -> bytes:
        encoded = password.encode("utf-8")
        minimum = MIN_PASSWORD_BYTES if require_minimum else 1
        if not minimum <= len(encoded) <= MAX_PASSWORD_BYTES:
            raise PasswordPolicyError(
                f"password must be {minimum}-{MAX_PASSWORD_BYTES} UTF-8 bytes"
            )
        return encoded

    def hash(self, password: str) -> str:
        encoded = self._bytes(password, require_minimum=True)
        return bcrypt.hashpw(encoded, bcrypt.gensalt(BCRYPT_COST)).decode("ascii")

    def verify(self, password: str, password_hash: str | None) -> bool:
        try:
            encoded = self._bytes(password, require_minimum=False)
        except PasswordPolicyError:
            encoded = b"invalid-overlong-password"
            password_hash = None
        selected_hash = password_hash.encode("ascii") if password_hash else self._dummy_hash
        try:
            matched = bcrypt.checkpw(encoded, selected_hash)
        except ValueError:
            matched = False
        return matched and password_hash is not None
