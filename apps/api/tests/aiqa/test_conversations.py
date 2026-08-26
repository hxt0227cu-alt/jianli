"""Round-2 integration tests: conversation persistence over the approved 0004 tables.

Requires a real PostgreSQL (``jianli_tc_aiqa_001_db``, schema already at head) and Redis.
Env: ``JIANLI_AIQA_TEST_DATABASE_URL`` + ``JIANLI_AIQA_TEST_REDIS_URL`` +
``JIANLI_CSRF_HMAC_KEY`` / ``JIANLI_RATE_LIMIT_HMAC_KEY`` (raw >=32 char strings).

Covers: create/list conversations, streamAnswer persistence (grounded + off-topic),
ownership (403 / 404), and auth boundaries (401 anonymous, 403 without CSRF).
"""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text

from app.auth.passwords import PasswordHasher
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import AuthRuntime, build_auth_runtime
from app.config import Settings
from app.factory import create_app

DATABASE_URL = os.environ.get("JIANLI_AIQA_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_AIQA_TEST_REDIS_URL")
ORIGIN = "https://aiqa.test"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


def _reset_database(engine: Engine) -> None:
    with engine.begin() as connection:
        # users CASCADE truncates auth_sessions/conversations (-> messages) transitively;
        # knowledge_documents CASCADE covers index versions. Cross-file isolation now that
        # round 3 grounds answers on the knowledge base.
        connection.execute(text("TRUNCATE TABLE users, knowledge_documents CASCADE"))


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
def real_stack() -> Iterator[tuple[Engine, Any, Settings]]:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    auth_runtime = build_auth_runtime(settings)
    app = create_app(settings, auth_runtime)
    try:
        yield engine, app, settings
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
    app: Any, engine: Engine, settings: Settings, user_id: UUID
) -> AsyncClient:
    session_token = secrets.token_urlsafe(32)
    auth_runtime: AuthRuntime = app.state.auth_runtime
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


def _events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.strip().split("\n\n"):
        event = ""
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
        if event and data_lines:
            events.append((event, json.loads("".join(data_lines))))
    return events


async def _stream_answer(
    client: AsyncClient, **body: object
) -> list[tuple[str, dict[str, object]]]:
    response = await client.post("/answers:stream", json=body)
    assert response.status_code == 200
    return _events(response.text)


@pytest.mark.asyncio
async def test_create_and_list_conversations(real_stack: Any) -> None:
    engine, app, settings = real_stack
    user = _seed_user(engine)
    async with _authorized_client(app, engine, settings, user) as client:
        response = await client.get("/conversations")
        assert response.status_code == 200
        assert response.json() == {"items": []}

        created = await client.post("/conversations")
        assert created.status_code == 201
        conversation = created.json()
        assert set(conversation) == {"id", "created_at", "updated_at"}

        listed = await client.get("/conversations")
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()["items"]] == [conversation["id"]]


@pytest.mark.asyncio
async def test_conversation_auth_boundaries(real_stack: Any) -> None:
    engine, app, settings = real_stack
    user = _seed_user(engine)
    # Anonymous session endpoints -> 401.
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anon:
        assert (await anon.get("/conversations")).status_code == 401
        assert (await anon.post("/conversations")).status_code == 401
        unknown = str(uuid4())
        assert (await anon.get(f"/conversations/{unknown}/messages")).status_code == 401
    # Authenticated but missing CSRF on POST -> 403.
    async with _authorized_client(app, engine, settings, user) as client:
        client.headers.pop("X-CSRF-Token")
        assert (await client.post("/conversations")).status_code == 403


@pytest.mark.asyncio
async def test_stream_answer_persists_grounded_messages(real_stack: Any) -> None:
    engine, app, settings = real_stack
    user = _seed_user(engine)
    async with _authorized_client(app, engine, settings, user) as client:
        conversation_id = (await client.post("/conversations")).json()["id"]
        events = await _stream_answer(
            client,
            question="你擅长什么技术方向？",
            page_key="resume",
            conversation_id=conversation_id,
        )
        started = events[0][1]
        assert started["conversation_id"] == conversation_id
        completed = events[-1][1]
        assert completed["grounded"] is True

        messages = (await client.get(f"/conversations/{conversation_id}/messages")).json()["items"]
        assert [message["role"] for message in messages] == ["user", "assistant"]
        assert messages[0]["content"] == "你擅长什么技术方向？"
        assert messages[0]["is_offtopic"] is False
        assert messages[1]["content"]
        assert messages[1]["is_offtopic"] is False
        with engine.connect() as connection:
            observed = connection.execute(
                text(
                    "SELECT grounded, citations_count, latency_ms "
                    "FROM conversation_messages "
                    "WHERE conv_id=:conversation_id AND role='assistant'"
                ),
                {"conversation_id": conversation_id},
            ).mappings().one()
        assert observed["grounded"] is True
        assert observed["citations_count"] > 0
        assert observed["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_stream_answer_persists_offtopic_flag(real_stack: Any) -> None:
    engine, app, settings = real_stack
    user = _seed_user(engine)
    async with _authorized_client(app, engine, settings, user) as client:
        conversation_id = (await client.post("/conversations")).json()["id"]
        events = await _stream_answer(
            client, question="今天天气怎么样？", page_key="resume", conversation_id=conversation_id
        )
        completed = events[-1][1]
        assert completed["offtopic"] is True
        messages = (await client.get(f"/conversations/{conversation_id}/messages")).json()["items"]
        assert messages[-1]["is_offtopic"] is True
        with engine.connect() as connection:
            observed = connection.execute(
                text(
                    "SELECT grounded, citations_count, latency_ms "
                    "FROM conversation_messages "
                    "WHERE conv_id=:conversation_id AND role='assistant'"
                ),
                {"conversation_id": conversation_id},
            ).mappings().one()
        assert observed["grounded"] is False
        assert observed["citations_count"] == 0
        assert observed["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_conversation_ownership_and_unknown(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine)
    other = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as owner_client:
        conversation_id = (await owner_client.post("/conversations")).json()["id"]
        async with _authorized_client(app, engine, settings, other) as other_client:
            response = await other_client.get(f"/conversations/{conversation_id}/messages")
            assert response.status_code == 403
            assert response.json()["code"] == "PERM_DENIED"
        unknown = str(uuid4())
        response = await owner_client.get(f"/conversations/{unknown}/messages")
        assert response.status_code == 404
        assert response.json()["code"] == "INVALID_REQUEST"
