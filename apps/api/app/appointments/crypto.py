from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .models import AppointmentDraft

SECURITY_LOGGER = logging.getLogger("jianli.security.booking")
ENVELOPE_VERSION = 1
NONCE_BYTES = 12
TAG_BYTES = 16


class BookingCryptoError(ValueError):
    pass


def _decode_key(value: str, label: str) -> bytes:
    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (binascii.Error, ValueError, UnicodeEncodeError) as error:
        raise ValueError(f"{label} must be URL-safe Base64") from error
    if base64.urlsafe_b64encode(decoded).decode("ascii") != value:
        raise ValueError(f"{label} must be canonical URL-safe Base64")
    if len(decoded) != 32:
        raise ValueError(f"{label} must decode to 32 bytes")
    return decoded


def _auth_key_material(value: str) -> bytes:
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        return value.encode("utf-8")
    return decoded if len(decoded) == 32 else value.encode("utf-8")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    if _b64encode(decoded) != value:
        raise ValueError("non-canonical Base64URL")
    return decoded


def normalize_company_name(value: str) -> str:
    return "".join(
        character.casefold()
        for character in value
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def canonical_payload_digest(payload: AppointmentDraft) -> str:
    canonical = json.dumps(
        payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class BookingSecrets:
    current_key_id: str
    field_keys: dict[str, bytes]
    company_hmac_key: bytes
    confirmation_hmac_key: bytes

    @classmethod
    def from_values(
        cls,
        *,
        current_key_id: str,
        field_keys: dict[str, str],
        company_hmac_key: str,
        confirmation_hmac_key: str,
        csrf_key: str,
        rate_limit_key: str,
    ) -> BookingSecrets:
        if not 1 <= len(field_keys) <= 2:
            raise ValueError("field key ring must contain one or two keys")
        if current_key_id not in field_keys or not current_key_id or len(current_key_id) > 255:
            raise ValueError("current field key id must identify a key in the ring")
        decoded_fields = {
            key_id: _decode_key(value, f"field key {key_id}")
            for key_id, value in field_keys.items()
        }
        company = _decode_key(company_hmac_key, "company HMAC key")
        confirmation = _decode_key(confirmation_hmac_key, "confirmation HMAC key")
        all_material = [
            *decoded_fields.values(),
            company,
            confirmation,
            _auth_key_material(csrf_key),
            _auth_key_material(rate_limit_key),
        ]
        if len(set(all_material)) != len(all_material):
            raise ValueError("AES, HMAC, CSRF, and rate-limit keys must be distinct")
        return cls(current_key_id, decoded_fields, company, confirmation)

    def company_fingerprint(self, company_name: str) -> str:
        normalized = normalize_company_name(company_name)
        if not normalized:
            raise BookingCryptoError("company name is empty after normalization")
        return hmac.new(
            self.company_hmac_key, normalized.encode("utf-8"), hashlib.sha256
        ).hexdigest()


class FieldCipher:
    def __init__(self, current_key_id: str, keys: dict[str, str] | dict[str, bytes]) -> None:
        decoded = {
            key_id: (_decode_key(value, f"field key {key_id}") if isinstance(value, str) else value)
            for key_id, value in keys.items()
        }
        if current_key_id not in decoded or not 1 <= len(decoded) <= 2:
            raise ValueError("invalid field key ring")
        self._current_key_id = current_key_id
        self._keys = decoded

    @staticmethod
    def _aad(table: str, column: str, record_id: UUID) -> bytes:
        return f"{table}\x00{column}\x00{record_id}".encode("ascii")

    def encrypt(self, plaintext: str, table: str, column: str, record_id: UUID) -> bytes:
        key_id = self._current_key_id.encode("utf-8")
        nonce = secrets.token_bytes(NONCE_BYTES)
        encrypted = AESGCM(self._keys[self._current_key_id]).encrypt(
            nonce, plaintext.encode("utf-8"), self._aad(table, column, record_id)
        )
        return bytes((ENVELOPE_VERSION, len(key_id))) + key_id + nonce + encrypted

    def envelope_key_id(self, envelope: bytes) -> str:
        if len(envelope) < 2 + NONCE_BYTES + TAG_BYTES or envelope[0] != ENVELOPE_VERSION:
            raise BookingCryptoError("invalid ciphertext envelope")
        key_id_length = envelope[1]
        try:
            return envelope[2 : 2 + key_id_length].decode("utf-8")
        except UnicodeDecodeError as error:
            raise BookingCryptoError("invalid ciphertext envelope") from error

    def decrypt(self, envelope: bytes, table: str, column: str, record_id: UUID) -> str:
        try:
            key_id = self.envelope_key_id(envelope)
            key = self._keys[key_id]
            offset = 2 + envelope[1]
            nonce = envelope[offset : offset + NONCE_BYTES]
            encrypted = envelope[offset + NONCE_BYTES :]
            if len(nonce) != NONCE_BYTES or len(encrypted) < TAG_BYTES:
                raise BookingCryptoError("invalid ciphertext envelope")
            return (
                AESGCM(key)
                .decrypt(nonce, encrypted, self._aad(table, column, record_id))
                .decode("utf-8")
            )
        except (KeyError, InvalidTag, UnicodeDecodeError, BookingCryptoError) as error:
            SECURITY_LOGGER.warning(
                json.dumps(
                    {
                        "event": "decrypt_failed",
                        "table": table,
                        "column": column,
                        "record_id": str(record_id),
                    },
                    separators=(",", ":"),
                )
            )
            raise BookingCryptoError("field decryption failed") from error


class ConfirmationTokens:
    def __init__(self, key: bytes) -> None:
        self._key = key

    def issue(
        self, user_id: UUID, payload_digest: str, now: datetime | None = None
    ) -> tuple[str, datetime]:
        issued_at = now or datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=3)
        claims = {
            "user_id": str(user_id),
            "payload_digest": payload_digest,
            "expires_at": int(expires_at.timestamp()),
            "nonce": _b64encode(secrets.token_bytes(32)),
        }
        body = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("ascii")
        signature = hmac.new(self._key, body, hashlib.sha256).digest()
        return f"{_b64encode(body)}.{_b64encode(signature)}", expires_at

    def verify(
        self, token: str, user_id: UUID, payload_digest: str, now: datetime | None = None
    ) -> None:
        try:
            body_text, signature_text = token.split(".", 1)
            body = _b64decode(body_text)
            signature = _b64decode(signature_text)
            expected = hmac.new(self._key, body, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise BookingCryptoError("invalid confirmation token")
            claims: dict[str, Any] = json.loads(body)
        except (ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise BookingCryptoError("invalid confirmation token") from error
        if claims.get("user_id") != str(user_id):
            raise BookingCryptoError("confirmation user mismatch")
        if claims.get("payload_digest") != payload_digest:
            raise BookingCryptoError("confirmation payload mismatch")
        current = now or datetime.now(UTC)
        if current.timestamp() >= int(claims.get("expires_at", 0)):
            raise BookingCryptoError("confirmation expired")
