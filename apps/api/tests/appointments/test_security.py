from __future__ import annotations

import base64
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.appointments.crypto import (
    BookingCryptoError,
    BookingSecrets,
    ConfirmationTokens,
    FieldCipher,
    canonical_payload_digest,
)
from app.appointments.models import AppointmentDraft


def _encoded_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def _draft() -> AppointmentDraft:
    return AppointmentDraft(
        slot_ids=[uuid4(), uuid4(), uuid4()],
        company_name="Example, Inc.",
        meeting_platform="Tencent Meeting",
        meeting_number="123-456-789",
        contact_last_name="Zhang",
        contact_salutation="Teacher",
        contact_phone="13800000000",
        notes="Private note",
    )


@pytest.mark.parametrize(
    "invalid_key",
    [
        base64.b64encode(b"\xfb" * 32).decode("ascii"),
        _encoded_key() + "!",
        _encoded_key().rstrip("="),
        _encoded_key() + "=",
    ],
)
def test_key_material_requires_canonical_urlsafe_base64(invalid_key: str) -> None:
    with pytest.raises(ValueError, match="URL-safe Base64"):
        FieldCipher("current", {"current": invalid_key})


def test_aes_gcm_random_nonce_and_aad_binding(caplog: pytest.LogCaptureFixture) -> None:
    cipher = FieldCipher("current", {"current": _encoded_key()})
    record_id = uuid4()
    first = cipher.encrypt("secret", "appointments", "notes_ciphertext", record_id)
    second = cipher.encrypt("secret", "appointments", "notes_ciphertext", record_id)

    assert first != second
    assert cipher.decrypt(first, "appointments", "notes_ciphertext", record_id) == "secret"
    with (
        caplog.at_level(logging.WARNING, logger="jianli.security.booking"),
        pytest.raises(BookingCryptoError),
    ):
        cipher.decrypt(first, "appointments", "contact_ciphertext", record_id)
    assert "decrypt_failed" in caplog.text
    assert "secret" not in caplog.text


def test_key_ring_is_current_write_and_current_previous_read() -> None:
    old_key = _encoded_key()
    new_key = _encoded_key()
    record_id = uuid4()
    old_cipher = FieldCipher("old", {"old": old_key})
    envelope = old_cipher.encrypt("legacy", "companies", "raw_name_ciphertext", record_id)

    rotating = FieldCipher("new", {"new": new_key, "old": old_key})
    assert rotating.decrypt(envelope, "companies", "raw_name_ciphertext", record_id) == "legacy"
    assert (
        rotating.envelope_key_id(
            rotating.encrypt("fresh", "companies", "raw_name_ciphertext", record_id)
        )
        == "new"
    )

    revoked = FieldCipher("new", {"new": new_key})
    with pytest.raises(BookingCryptoError):
        revoked.decrypt(envelope, "companies", "raw_name_ciphertext", record_id)


def test_fingerprint_and_confirmation_token_binding() -> None:
    secrets_config = BookingSecrets.from_values(
        current_key_id="field",
        field_keys={"field": _encoded_key()},
        company_hmac_key=_encoded_key(),
        confirmation_hmac_key=_encoded_key(),
        csrf_key=secrets.token_urlsafe(32),
        rate_limit_key=secrets.token_urlsafe(32),
    )
    assert secrets_config.company_fingerprint(
        " Example, Inc. "
    ) == secrets_config.company_fingerprint("example inc")

    tokens = ConfirmationTokens(secrets_config.confirmation_hmac_key)
    user_id = uuid4()
    draft = _draft()
    now = datetime.now(UTC)
    token, expires_at = tokens.issue(user_id, canonical_payload_digest(draft), now)
    tokens.verify(token, user_id, canonical_payload_digest(draft), now + timedelta(seconds=1))
    assert expires_at == now + timedelta(minutes=3)

    changed = draft.model_copy(update={"meeting_number": "changed"})
    with pytest.raises(BookingCryptoError, match="confirmation payload mismatch"):
        tokens.verify(token, user_id, canonical_payload_digest(changed), now)
    with pytest.raises(BookingCryptoError, match="confirmation user mismatch"):
        tokens.verify(token, uuid4(), canonical_payload_digest(draft), now)
    with pytest.raises(BookingCryptoError, match="confirmation expired"):
        tokens.verify(token, user_id, canonical_payload_digest(draft), expires_at)
    with pytest.raises(BookingCryptoError, match="invalid confirmation token"):
        tokens.verify(
            token[:-1] + ("A" if token[-1] != "A" else "B"),
            user_id,
            canonical_payload_digest(draft),
            now,
        )


def test_startup_rejects_reused_or_invalid_key_material() -> None:
    shared = _encoded_key()
    with pytest.raises(ValueError, match="distinct"):
        BookingSecrets.from_values(
            current_key_id="field",
            field_keys={"field": shared},
            company_hmac_key=shared,
            confirmation_hmac_key=_encoded_key(),
            csrf_key=secrets.token_urlsafe(32),
            rate_limit_key=secrets.token_urlsafe(32),
        )
    with pytest.raises(ValueError, match="one or two"):
        BookingSecrets.from_values(
            current_key_id="field",
            field_keys={"field": _encoded_key(), "old": _encoded_key(), "older": _encoded_key()},
            company_hmac_key=_encoded_key(),
            confirmation_hmac_key=_encoded_key(),
            csrf_key=secrets.token_urlsafe(32),
            rate_limit_key=secrets.token_urlsafe(32),
        )
