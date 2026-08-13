"""Round-3 integration tests: knowledge-base ingestion + pgvector grounding.

Requires a real PostgreSQL with the pgvector extension (0005) + Redis. Same env as
``test_conversations.py``: ``JIANLI_AIQA_TEST_DATABASE_URL`` (``jianli_tc_aiqa_001_db``,
already at head) + ``JIANLI_AIQA_TEST_REDIS_URL`` + CSRF/RATE_LIMIT HMAC keys.

Covers: md/txt upload → indexing status, active-checksum dedupe, unsupported-type
failure, admin-only permissions, knowledge grounding in ``streamAnswer``, and delete
(immediately disabled from retrieval).
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
        connection.execute(text("TRUNCATE TABLE users, knowledge_documents CASCADE"))


def _pdf_bytes(text: str) -> bytes:
    """Minimal valid single-page PDF with an ASCII text line (no extra deps)."""

    content = f"BT /F1 12 Tf 50 760 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets: list[int] = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii") + b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode("ascii")
    return out


def _settings(storage_dir: str) -> Settings:
    assert DATABASE_URL and REDIS_URL
    return Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        csrf_hmac_key=os.environ["JIANLI_CSRF_HMAC_KEY"],
        rate_limit_hmac_key=os.environ["JIANLI_RATE_LIMIT_HMAC_KEY"],
        allowed_origins=(ORIGIN,),
        knowledge_storage_dir=storage_dir,
    )


@pytest.fixture
def real_stack(tmp_path: Any) -> Iterator[tuple[Engine, Any, Settings]]:
    settings = _settings(str(tmp_path / "knowledge"))
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


def _upload(client: AsyncClient, files: list[tuple[str, bytes]]) -> Any:
    payload = [("files", (name, content, "text/markdown")) for name, content in files]
    return client.post("/admin/knowledge-documents", files=payload)


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
    client: AsyncClient, question: str
) -> list[tuple[str, dict[str, object]]]:
    response = await client.post(
        "/answers:stream", json={"question": question, "page_key": "resume"}
    )
    assert response.status_code == 200
    return _events(response.text)


@pytest.mark.asyncio
async def test_upload_index_dedupe_and_unsupported(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    content = "# 简介\n我擅长分布式系统设计与高并发服务。".encode()
    async with _authorized_client(app, engine, settings, owner) as client:
        response = await _upload(client, [("resume.md", content)])
        assert response.status_code == 202
        # Same content again is deduped (active checksum unique index) -> still 1 active row.
        response = await _upload(client, [("resume-copy.md", content)])
        assert response.status_code == 202
        # Unsupported type is recorded as failed, not rejected. docx is still unsupported
        # (PDF became supported in TASK-KB-PDF-001; corrupt-PDF handling has its own case).
        response = await _upload(client, [("notes.docx", b"PK fake docx")])
        assert response.status_code == 202

        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        by_name = {item["name"]: item for item in listed}
        assert by_name["resume.md"]["status"] == "indexed"
        assert by_name["resume.md"]["type"] == "md"
        assert by_name["notes.docx"]["status"] == "failed"
        assert "not supported" in by_name["notes.docx"]["failure_reason"]
        assert "resume-copy.md" not in by_name


@pytest.mark.asyncio
async def test_knowledge_grounds_answer(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    skills = "# 技能\n我擅长分布式系统设计与高并发服务。".encode()
    async with _authorized_client(app, engine, settings, owner) as client:
        await _upload(client, [("skills.md", skills)])
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anon:
        events = await _stream_answer(anon, "你擅长什么技术？")
        assert events[-1][1]["grounded"] is True
        citations = next(d for name, d in events if name == "answer.citations")
        assert any(cite["doc"] == "skills.md" for cite in citations["citations"])


@pytest.mark.asyncio
async def test_delete_disables_retrieval(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    keyword = "云原生向量检索独角兽"
    async with _authorized_client(app, engine, settings, owner) as client:
        await _upload(client, [("unique.md", f"# 秘密\n{keyword} 是我的独家关键词。".encode())])
        doc_id = (await client.get("/admin/knowledge-documents")).json()["items"][0]["id"]
        before = await _stream_answer(client, keyword)
        assert before[-1][1]["grounded"] is True
        before_citations = next(d for name, d in before if name == "answer.citations")
        assert any(cite["doc"] == "unique.md" for cite in before_citations["citations"])

        deleted = await client.delete(f"/admin/knowledge-documents/{doc_id}")
        assert deleted.status_code == 204

        # Retrieval is disabled at the DB level (domain model §6.14: delete = immediately
        # disable retrieval).
        with engine.connect() as connection:
            disabled = connection.scalar(
                text(
                    "SELECT retrieval_disabled_at IS NOT NULL "
                    "FROM knowledge_documents WHERE id=:id"
                ),
                {"id": doc_id},
            )
        assert disabled is True

        # The deleted document must never appear as a citation again. NOTE: the static
        # page fallback may still ground a query (e.g. "检索" overlaps resume content),
        # so we assert absence of the document, not offtopic.
        after = await _stream_answer(client, keyword)
        after_citations = next(d for name, d in after if name == "answer.citations")
        assert all(cite["doc"] != "unique.md" for cite in after_citations["citations"])


@pytest.mark.asyncio
async def test_upload_pdf_indexes_and_grounds(real_stack: Any) -> None:
    """Resume PDFs upload with parse_mode=native and ground answers (TASK-KB-PDF-001)."""

    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    pdf = _pdf_bytes("I am good at distributed systems and high concurrency services")
    async with _authorized_client(app, engine, settings, owner) as client:
        response = await _upload(client, [("resume.pdf", pdf)])
        assert response.status_code == 202
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        by_name = {item["name"]: item for item in listed}
        assert by_name["resume.pdf"]["status"] == "indexed"
        assert by_name["resume.pdf"]["type"] == "pdf"
        assert by_name["resume.pdf"]["parse_mode"] == "native"
        # Same PDF content again is deduped (active checksum unique index).
        await _upload(client, [("resume-copy.pdf", pdf)])
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        assert len([item for item in listed if item["name"].endswith(".pdf")]) == 1
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anon:
        events = await _stream_answer(anon, "distributed systems")
        assert events[-1][1]["grounded"] is True
        citations = next(d for name, d in events if name == "answer.citations")
        assert any(cite["doc"] == "resume.pdf" for cite in citations["citations"])


@pytest.mark.asyncio
async def test_upload_corrupt_pdf_fails_with_reason(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    async with _authorized_client(app, engine, settings, owner) as client:
        response = await _upload(client, [("broken.pdf", b"%PDF-1.4 not a real pdf")])
        assert response.status_code == 202
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        broken = next(item for item in listed if item["name"] == "broken.pdf")
        assert broken["status"] == "failed"
        assert "PDF parse failed" in broken["failure_reason"]


@pytest.mark.asyncio
async def test_knowledge_permissions(real_stack: Any) -> None:
    engine, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    interviewer = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as owner_client:
        await _upload(owner_client, [("a.md", b"owner content")])
        async with _authorized_client(app, engine, settings, interviewer) as viewer:
            assert (await viewer.get("/admin/knowledge-documents")).status_code == 403
            assert (await _upload(viewer, [("b.md", b"x")])).status_code == 403
            doc_id = (await owner_client.get("/admin/knowledge-documents")).json()["items"][0]["id"]
            assert (await viewer.delete(f"/admin/knowledge-documents/{doc_id}")).status_code == 403
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anon:
        assert (await anon.get("/admin/knowledge-documents")).status_code == 401
        assert (await _upload(anon, [("c.md", b"y")])).status_code == 401
