"""Integration tests for updateOwnerContactConfig (R13 Feishu open_id config entry).

Covers: upsert semantics (insert then update), AES ciphertext at rest with decryption
round-trip, RBAC (owner_admin only), CSRF enforcement, and the no-active-owner_admin
failure path (default Error, never silently succeeds).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text

from app.appointments.crypto import FieldCipher
from app.appointments.runtime import build_booking_runtime
from app.auth.passwords import PasswordHasher
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")
ORIGIN = "https://booking.test"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


def _reset_database(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE audit_logs, notification_events, users, companies CASCADE")
        )


def _settings() -> Settings:
    assert DATABASE_URL and REDIS_URL
    return Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        csrf_hmac_key=os.environ["JIANLI_CSRF_HMAC_KEY"],
        rate_limit_hmac_key=os.environ["JIANLI_RATE_LIMIT_HMAC_KEY"],
        allowed_origins=(ORIGIN,),
        field_encryption_current_key_id=os.environ["JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID"],
        field_encryption_keys=os.environ["JIANLI_FIELD_ENCRYPTION_KEYS"],
        company_fingerprint_hmac_key=os.environ["JIANLI_COMPANY_FINGERPRINT_HMAC_KEY"],
        appointment_confirmation_hmac_key=os.environ["JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY"],
    )


@pytest.fixture
def real_stack() -> tuple[Engine, redis.Redis, object, Settings]:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    auth_runtime = build_auth_runtime(settings)
    booking_runtime = build_booking_runtime(settings, auth_runtime)
    app = create_app(settings, auth_runtime, booking_runtime)
    try:
        yield engine, redis_client, app, settings
    finally:
        auth_runtime.close()
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


def _seed_user(engine: Engine, role: str = "interviewer") -> UUID:
    user_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:password_hash,:role,true)"
            ),
            {
                "id": user_id,
                "email": f"{user_id}@example.invalid",
                "password_hash": PasswordHasher().hash("correct-password"),
                "role": role,
            },
        )
    return user_id


def _authorized_client(
    app: object, engine: Engine, settings: Settings, user_id: UUID
) -> AsyncClient:
    import secrets

    session_token = secrets.token_urlsafe(32)
    auth_runtime = app.state.auth_runtime
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO auth_sessions "
                "(id,user_id,session_token_hash,expires_at,revoked_at) "
                "VALUES (:id,:user_id,:token_hash,:expires_at,NULL)"
            ),
            {
                "id": uuid4(),
                "user_id": user_id,
                "token_hash": auth_runtime.tokens.digest(session_token),
                "expires_at": datetime.now(UTC) + timedelta(hours=1),
            },
        )
    csrf = auth_runtime.tokens.csrf(session_token)
    client = AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN)
    client.cookies.set(SESSION_COOKIE, session_token)
    client.cookies.set(CSRF_COOKIE, csrf)
    client.headers.update({"Origin": ORIGIN, "X-CSRF-Token": csrf})
    return client


def _config_row(engine: Engine) -> dict[str, object] | None:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT id,user_id,candidate_feishu_open_id_ciphertext "
                "FROM owner_contact_configs"
            )
        ).mappings().one_or_none()
    return dict(row) if row else None


def _decrypt(settings: Settings, config_id: UUID, ciphertext: bytes) -> str:
    key_ring = json.loads(settings.field_encryption_keys.get_secret_value())
    cipher = FieldCipher(settings.field_encryption_current_key_id, key_ring)
    return cipher.decrypt(
        ciphertext, "owner_contact_configs", "candidate_feishu_open_id_ciphertext", config_id
    )


@pytest.mark.asyncio
async def test_config_insert_then_update_upserts_encrypted(real_stack) -> None:
    engine, _redis, app, settings = real_stack
    owner = _seed_user(engine, role="owner_admin")

    async with _authorized_client(app, engine, settings, owner) as client:
        first = await client.put(
            "/admin/owner-contact-config",
            json={"candidate_feishu_open_id": "ou_first_001"},
        )
        assert first.status_code == 200, first.text
        assert first.json() == {"configured": True}

        row = _config_row(engine)
        assert row is not None
        assert row["user_id"] == owner
        # ciphertext at rest: stored value must NOT be the plaintext open_id
        assert row["candidate_feishu_open_id_ciphertext"] != b"ou_first_001"
        decrypted = _decrypt(settings, row["id"], row["candidate_feishu_open_id_ciphertext"])
        assert decrypted == "ou_first_001"

        second = await client.put(
            "/admin/owner-contact-config",
            json={"candidate_feishu_open_id": "ou_second_002"},
        )
        assert second.status_code == 200, second.text

        row2 = _config_row(engine)
        assert row2 is not None and row2["id"] == row["id"]  # same row, updated
        decrypted2 = _decrypt(settings, row2["id"], row2["candidate_feishu_open_id_ciphertext"])
        assert decrypted2 == "ou_second_002"


@pytest.mark.asyncio
async def test_config_requires_owner_admin_role(real_stack) -> None:
    engine, _redis, app, settings = real_stack
    interviewer = _seed_user(engine, role="interviewer")

    async with _authorized_client(app, engine, settings, interviewer) as client:
        response = await client.put(
            "/admin/owner-contact-config",
            json={"candidate_feishu_open_id": "ou_hacker_001"},
        )
    assert response.status_code == 403
    assert _config_row(engine) is None


@pytest.mark.asyncio
async def test_config_requires_csrf(real_stack) -> None:
    engine, _redis, app, settings = real_stack
    owner = _seed_user(engine, role="owner_admin")

    async with _authorized_client(app, engine, settings, owner) as client:
        client.headers.pop("X-CSRF-Token")
        response = await client.put(
            "/admin/owner-contact-config",
            json={"candidate_feishu_open_id": "ou_no_csrf"},
        )
    assert response.status_code == 403
    assert _config_row(engine) is None


@pytest.mark.asyncio
async def test_config_fails_without_active_owner_admin(real_stack) -> None:
    engine, _redis, _app, settings = real_stack
    # Only an interviewer exists; no active owner_admin. A valid owner_admin session
    # implies an active owner_admin row (auth principal joins users.deleted_at IS NULL),
    # so the no-owner branch is not reachable over HTTP — assert at the service layer.
    from app.appointments.runtime import build_booking_runtime
    from app.appointments.service import AuthError
    from app.auth.runtime import build_auth_runtime

    auth_runtime = build_auth_runtime(settings)
    booking = build_booking_runtime(settings, auth_runtime)
    try:
        with pytest.raises(AuthError) as exc:
            booking.update_owner_contact_config("ou_orphan_001")
        assert exc.value.code == "NOT_CONFIGURABLE"
    finally:
        auth_runtime.close()
    assert _config_row(engine) is None


@pytest.mark.asyncio
async def test_config_rejects_blank_open_id(real_stack) -> None:
    engine, _redis, app, settings = real_stack
    owner = _seed_user(engine, role="owner_admin")

    async with _authorized_client(app, engine, settings, owner) as client:
        response = await client.put(
            "/admin/owner-contact-config",
            json={"candidate_feishu_open_id": "ab"},  # minLength=5
        )
    assert response.status_code == 422
    assert _config_row(engine) is None
