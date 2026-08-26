from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text

from app.appointments.runtime import build_booking_runtime
from app.auth.passwords import PasswordHasher
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")
ORIGIN = "https://admin-qa.test"

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
        field_encryption_current_key_id=os.environ["JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID"],
        field_encryption_keys=os.environ["JIANLI_FIELD_ENCRYPTION_KEYS"],
        company_fingerprint_hmac_key=os.environ["JIANLI_COMPANY_FINGERPRINT_HMAC_KEY"],
        appointment_confirmation_hmac_key=os.environ[
            "JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY"
        ],
    )


@pytest.fixture
def real_stack() -> tuple[Engine, object]:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))
    auth_runtime = build_auth_runtime(settings)
    booking_runtime = build_booking_runtime(settings, auth_runtime)
    app = create_app(settings, auth_runtime, booking_runtime)
    try:
        yield engine, app
    finally:
        auth_runtime.close()
        redis_client.close()
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE users CASCADE"))
        engine.dispose()


def _seed_user(engine: Engine, role: str) -> UUID:
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


def _client(app: object, engine: Engine, user_id: UUID) -> AsyncClient:
    session_token = secrets.token_urlsafe(32)
    runtime = app.state.auth_runtime
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
                "token_hash": runtime.tokens.digest(session_token),
                "expires_at": datetime.now(UTC) + timedelta(hours=1),
            },
        )
    csrf = runtime.tokens.csrf(session_token)
    client = AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN)
    client.cookies.set(SESSION_COOKIE, session_token)
    client.cookies.set(CSRF_COOKIE, csrf)
    client.headers.update({"Origin": ORIGIN})
    return client


def _seed_conversation(engine: Engine, user_id: UUID) -> UUID:
    conversation_id = uuid4()
    now = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO conversations (id,user_id,created_at,updated_at) "
                "VALUES (:id,:user_id,:now,:now)"
            ),
            {"id": conversation_id, "user_id": user_id, "now": now},
        )
        for role, content, is_offtopic in (
            ("user", "你在 Agent 工具越权方面做了什么？", False),
            ("assistant", "工具白名单与 BookingService RBAC 双重约束。", False),
        ):
            connection.execute(
                text(
                    "INSERT INTO conversation_messages "
                    "(id,conv_id,role,content,is_offtopic,created_at) "
                    "VALUES (:id,:conv_id,:role,:content,:is_offtopic,:now)"
                ),
                {
                    "id": uuid4(),
                    "conv_id": conversation_id,
                    "role": role,
                    "content": content,
                    "is_offtopic": is_offtopic,
                    "now": now,
                },
            )
    return conversation_id


@pytest.mark.asyncio
async def test_owner_reads_question_history_and_interviewer_is_denied(real_stack) -> None:
    engine, app = real_stack
    owner_id = _seed_user(engine, "owner_admin")
    interviewer_id = _seed_user(engine, "interviewer")
    conversation_id = _seed_conversation(engine, interviewer_id)

    paths = (
        "/admin/conversations",
        f"/admin/conversations/{conversation_id}/messages",
        "/admin/aiqa-stats",
    )
    async with _client(app, engine, interviewer_id) as interviewer:
        for path in paths:
            denied = await interviewer.get(path)
            assert denied.status_code == 403
            assert denied.json()["code"] == "PERM_DENIED"

    async with _client(app, engine, owner_id) as owner:
        conversations = await owner.get(paths[0])
        messages = await owner.get(paths[1])
        stats = await owner.get(paths[2])

    assert conversations.status_code == 200
    assert conversations.json()["items"][0]["message_count"] == 2
    assert messages.status_code == 200
    assert [item["role"] for item in messages.json()["items"]] == ["user", "assistant"]
    assert messages.json()["items"][0]["content"].startswith("你在 Agent")
    assert stats.status_code == 200
    assert stats.json()["totals"]["total_conversations"] == 1
    assert stats.json()["totals"]["total_messages"] == 2
