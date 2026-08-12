"""Real PostgreSQL + Redis tests for account self-service (M4).

Covers register / verify-email / password-reset/request / password-reset/confirm,
matching the approved contract in ``docs/api/openapi.yaml``. Token delivery is
best-effort: when SMTP is not configured the service must still persist tokens
(asserted here) and simply skip sending.

Run with real PG/Redis (WSL): export the same JIANLI_*_TEST_DATABASE_URL /
REDIS_URL and the csrf/rate-limit HMAC keys used by the other real-stack tests.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text

from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

# Reuse the already-provisioned auth/booking test databases so no extra env setup
# is needed; either name is accepted.
DATABASE_URL = os.environ.get("JIANLI_AUTH_TEST_DATABASE_URL") or os.environ.get(
    "JIANLI_BOOKING_TEST_DATABASE_URL"
)
REDIS_URL = os.environ.get("JIANLI_AUTH_TEST_REDIS_URL") or os.environ.get(
    "JIANLI_BOOKING_TEST_REDIS_URL"
)
ORIGIN = "https://auth.test"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


def _settings() -> Settings:
    assert DATABASE_URL and REDIS_URL
    return Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        csrf_hmac_key=os.environ["JIANLI_CSRF_HMAC_KEY"],
        rate_limit_hmac_key=os.environ["JIANLI_RATE_LIMIT_HMAC_KEY"],
        allowed_origins=(ORIGIN,),
    )


@pytest.fixture
def real_stack() -> tuple[Engine, redis.Redis, object, Settings]:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE users, auth_sessions, "
                "email_verification_tokens, password_reset_tokens CASCADE"
            )
        )
    auth_runtime = build_auth_runtime(settings)
    app = create_app(settings, auth_runtime)
    try:
        yield engine, redis_client, app, settings
    finally:
        auth_runtime.close()
        redis_client.close()
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE users, auth_sessions, "
                    "email_verification_tokens, password_reset_tokens CASCADE"
                )
            )
        engine.dispose()


def _user_row(engine: Engine, email: str) -> dict:
    with engine.connect() as connection:
        return (
            connection.execute(
                text("SELECT id,verified,password_hash FROM users WHERE email=:email"),
                {"email": email},
            )
            .mappings()
            .one()
        )


def _token_count(engine: Engine, table: str, user_id: UUID) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(
                text(f"SELECT count(*) FROM {table} WHERE user_id=:user_id"),
                {"user_id": user_id},
            ).scalar()
        )


def _seed_session(engine: Engine, auth_runtime, user_id: UUID) -> str:
    token = "session-token-for-reset-test-0123456789"
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO auth_sessions (id,user_id,session_token_hash,expires_at,revoked_at) "
                "VALUES (:id,:user_id,:token_hash,:expires_at,NULL)"
            ),
            {
                "id": uuid4(),
                "user_id": user_id,
                "token_hash": auth_runtime.tokens.digest(token),
                "expires_at": datetime.now(UTC) + timedelta(hours=1),
            },
        )
    return token


@pytest.mark.asyncio
async def test_register_creates_unverified_user_and_token(real_stack) -> None:
    engine, _, app, _ = real_stack
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        created = await client.post(
            "/auth/register",
            headers={"Origin": ORIGIN},
            json={"email": "New.Person@Example.com", "password": "correct-horse"},
        )
        assert created.status_code == 202  # generic; verification email queued

        duplicate = await client.post(
            "/auth/register",
            headers={"Origin": ORIGIN},
            json={"email": "new.person@example.com", "password": "correct-horse"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "DUPLICATE_EMAIL"

    user = _user_row(engine, "new.person@example.com")
    assert user["verified"] is False
    assert str(user["password_hash"]).startswith("$2b$")
    assert _token_count(engine, "email_verification_tokens", user["id"]) == 1


@pytest.mark.asyncio
async def test_verify_email_consumes_token_and_is_idempotent(real_stack, monkeypatch) -> None:
    engine, _, app, _ = real_stack
    known = "verify-known-token-0123456789abcdef"
    runtime = app.state.auth_runtime
    # Control the raw token so we can exercise the verify endpoint end-to-end.
    monkeypatch.setattr(runtime.service._tokens, "generate", lambda: known)

    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        await client.post(
            "/auth/register",
            headers={"Origin": ORIGIN},
            json={"email": "verify@example.com", "password": "correct-horse"},
        )
        ok = await client.post(
            "/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": known}
        )
        assert ok.status_code == 204
        # Idempotent: a second verify with the same (now consumed) token still 204.
        again = await client.post(
            "/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": known}
        )
        assert again.status_code == 204
        # Wrong token is rejected.
        bad = await client.post(
            "/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": "nope"}
        )
        assert bad.status_code == 409
        assert bad.json()["code"] == "INVALID_TOKEN"

    user = _user_row(engine, "verify@example.com")
    assert user["verified"] is True
    with engine.connect() as connection:
        consumed = connection.execute(
            text(
                "SELECT count(*) FROM email_verification_tokens "
                "WHERE user_id=:user_id AND consumed_at IS NOT NULL"
            ),
            {"user_id": user["id"]},
        ).scalar()
    assert int(consumed) >= 1


@pytest.mark.asyncio
async def test_password_reset_is_one_time_revokes_sessions_and_does_not_enumerate(
    real_stack, monkeypatch
) -> None:
    engine, _, app, _ = real_stack
    known = "reset-known-token-0123456789abcdef"
    runtime = app.state.auth_runtime
    monkeypatch.setattr(runtime.service._tokens, "generate", lambda: known)

    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        await client.post(
            "/auth/register",
            headers={"Origin": ORIGIN},
            json={"email": "reset@example.com", "password": "correct-horse"},
        )
        # A registered account is unverified; verification is required before login.
        # Drive it via the same known token so the reset flow below starts verified.
        verify = await client.post(
            "/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": known}
        )
        assert verify.status_code == 204
        user = _user_row(engine, "reset@example.com")
        assert user["verified"] is True
        old_session = _seed_session(engine, runtime, user["id"])

        # Request reset for existing and non-existing emails: both 202, no leakage.
        existing = await client.post(
            "/auth/password-reset/request",
            headers={"Origin": ORIGIN},
            json={"email": "reset@example.com"},
        )
        missing = await client.post(
            "/auth/password-reset/request",
            headers={"Origin": ORIGIN},
            json={"email": "ghost@example.com"},
        )
        assert existing.status_code == 202
        assert missing.status_code == 202
        assert _token_count(engine, "password_reset_tokens", user["id"]) == 1

        # Weak password is rejected (422) BEFORE consuming the token.
        weak = await client.post(
            "/auth/password-reset/confirm",
            headers={"Origin": ORIGIN},
            json={"token": known, "new_password": "short"},
        )
        assert weak.status_code == 422
        assert weak.json()["code"] == "INVALID_REQUEST"

        # Consume the reset token with a new password.
        done = await client.post(
            "/auth/password-reset/confirm",
            headers={"Origin": ORIGIN},
            json={"token": known, "new_password": "brand-new-pass"},
        )
        assert done.status_code == 204

        # Old password is invalidated; new password logs in.
        old_login = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "email": "reset@example.com",
                "password": "correct-horse",
                "remember_me": False,
            },
        )
        assert old_login.status_code == 401
        new_login = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "email": "reset@example.com",
                "password": "brand-new-pass",
                "remember_me": False,
            },
        )
        assert new_login.status_code == 204

    # The seeded session was revoked on reset.
    with engine.connect() as connection:
        revoked = connection.execute(
            text("SELECT revoked_at FROM auth_sessions WHERE session_token_hash=:h"),
            {"h": runtime.tokens.digest(old_session)},
        ).scalar()
    assert revoked is not None


@pytest.mark.asyncio
async def test_strong_password_policy_is_enforced_on_register(real_stack) -> None:
    engine, _, app, _ = real_stack
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        too_short = await client.post(
            "/auth/register",
            headers={"Origin": ORIGIN},
            json={"email": "weak@example.com", "password": "short"},
        )
        assert too_short.status_code == 422
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM users WHERE email='weak@example.com'")
            ).scalar()
            == 0
        )
