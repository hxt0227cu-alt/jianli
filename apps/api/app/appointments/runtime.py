"""Appointment runtime wiring over the existing auth engine and Redis client."""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.auth.runtime import AuthRuntime
from app.config import Settings

from .crypto import BookingSecrets
from .service import BookingService


@dataclass(slots=True)
class BookingRuntime:
    service: BookingService


def build_booking_runtime(settings: Settings, auth_runtime: AuthRuntime) -> BookingRuntime:
    if not settings.booking_configured:
        raise ValueError("complete booking settings are required")
    assert settings.field_encryption_current_key_id
    assert settings.field_encryption_keys
    assert settings.company_fingerprint_hmac_key
    assert settings.appointment_confirmation_hmac_key
    assert settings.csrf_hmac_key and settings.rate_limit_hmac_key
    try:
        key_ring = json.loads(settings.field_encryption_keys.get_secret_value())
    except json.JSONDecodeError as error:
        raise ValueError("field encryption keys must be a JSON object") from error
    if not isinstance(key_ring, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in key_ring.items()
    ):
        raise ValueError("field encryption keys must be a string-to-string JSON object")
    secrets_config = BookingSecrets.from_values(
        current_key_id=settings.field_encryption_current_key_id,
        field_keys=key_ring,
        company_hmac_key=settings.company_fingerprint_hmac_key.get_secret_value(),
        confirmation_hmac_key=settings.appointment_confirmation_hmac_key.get_secret_value(),
        csrf_key=settings.csrf_hmac_key.get_secret_value(),
        rate_limit_key=settings.rate_limit_hmac_key.get_secret_value(),
    )
    return BookingRuntime(
        BookingService(
            auth_runtime.engine,
            secrets_config,
            auth_runtime.redis_client,
            settings.rate_limit_hmac_key.get_secret_value(),
        )
    )
