"""RAG evaluation suite (TASK-RAG-EVAL-001): quantify retrieval quality.

Requires a real PostgreSQL (pgvector at head 0006) + Redis — same env as
``test_knowledge.py``: ``JIANLI_AIQA_TEST_DATABASE_URL`` (``jianli_tc_aiqa_001_db``)
+ ``JIANLI_AIQA_TEST_REDIS_URL`` + CSRF/RATE_LIMIT HMAC keys.

Structure (14 cases):
- 8 hit cases: a question whose keywords live in one corpus doc must return
  ``grounded=True`` and cite that document (doc-level recall through the full
  upload → chunk → hybrid-retrieval pipeline).
- 6 reject cases: out-of-scope or not-in-resume questions must be refused
  (``offtopic=True``). They are **xfail** on purpose: retrieval has no relevance
  threshold yet (P1), so vector top-k hard-recalls even irrelevant questions —
  the evaluation makes that defect explicit and quantifiable (reject rate 0% is
  the "before" baseline that P1 must turn green).
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

# ---------------------------------------------------------------------------
# Evaluation corpus (4 Chinese markdown docs, keyword-distributed). The text is
# deliberately kept under one chunk each (~<500 chars) so a hit maps to one doc.
# ---------------------------------------------------------------------------

CORPUS: dict[str, str] = {
    "resume.md": (
        "# [姓名已脱敏] · 个人简历\n"
        "## 教育背景\n"
        "[学校已脱敏]（公办本科）计算机科学与技术专业，专业排名 3/153，"
        "GPA 3.38/4.0，中共党员。\n"
        "## 技术栈\n"
        "精通 Python 与 FastAPI 后端开发，熟悉 RAG 检索增强生成与 AI Agent "
        "编排，使用过 LangGraph、pgvector、Milvus 向量数据库。"
    ),
    "honors.md": (
        "# 荣誉证书与实习经历\n"
        "获得 2025 年国家奖学金，2024 年大创国家级立项第一负责人，挑战杯 A 类"
        "赛事路演资格，TiDB 数据库专员 PCTA 认证，大学英语四级 CET4。\n"
        "## 实习\n"
        "2023 年在掌大传媒担任运营实习生，负责用户痛点发掘与业务落地。"
    ),
    "litchi.md": (
        "# Litchi Copilot 荔枝智能农技协同平台\n"
        "面向农户、农资门店与农业技术员的 AI 业务闭环，围绕病害识别、证据检索、"
        "方案推荐、人工审核、门店履约、效果反馈构建。\n"
        "## 受控 Agent 架构\n"
        "设计 Planner 规划器、Guard 守卫、Executor 执行器、Synthesizer 合成器"
        "四阶段受控 Agent 管线，封装知识检索、图谱查询、果园上下文等工具，"
        "通过白名单、RBAC、步骤预算和 HITL 人工审批控制越权与高风险写操作。\n"
        "## 技术选型\n"
        "使用 Milvus 与 Neo4j 融合文档证据与病虫害关系数据，构建 RAG 检索增强"
        "链路；通过 SSE 事件流、Checkpoint 检查点、Prometheus 指标实现过程追踪。"
    ),
    "taiyizhi.md": (
        "# 泰益智医疗 睡眠健康 AIoT Agent Harness\n"
        "面向睡眠监测、分析、建议、设备干预、效果反馈的 Agent 平台，将模型能力"
        "封装为可调用、可审批、可恢复、可评测的服务。\n"
        "## 分层架构\n"
        "LangGraph 负责有界推理，Temporal 负责长任务编排、审批取消信号与失败"
        "重试，PostgreSQL 作为运行状态权威；通过稳定 Workflow ID 与步骤、工具、"
        "Token 预算控制重复执行。\n"
        "## RAG 与安全\n"
        "实现 Embedding 加 pgvector 多租户 RAG，覆盖文档切分、向量检索、租户"
        "隔离、引用约束；建立最小权限工具体系，设备写操作必须 HITL 审批，"
        "Prompt Injection 注入攻击 10 例全部拦截。"
    ),
}

# (question, expected_doc) — question keywords must literally appear in the doc
# so the BM25 half of the hybrid retrieval can ground it.
HIT_CASES: list[tuple[str, str]] = [
    ("[姓名已脱敏]在哪个大学读书？", "resume.md"),
    ("你的技术栈包括哪些？", "resume.md"),
    ("你获得过什么荣誉？", "honors.md"),
    ("Litchi Copilot 的 Agent 架构是什么？", "litchi.md"),
    ("Litchi 用了什么向量数据库？", "litchi.md"),
    ("泰益智项目用什么做任务编排？", "taiyizhi.md"),
    ("你的 RAG 是怎么做租户隔离的？", "taiyizhi.md"),
    ("泰益智项目怎么防 Prompt Injection？", "taiyizhi.md"),
]

# Out-of-scope or not-in-corpus questions: must be refused (offtopic=True).
# xfail until P1 adds a relevance threshold to hybrid retrieval.
REJECT_CASES: list[str] = [
    "帮我写一个爬虫脚本抓取微博数据",
    "今天天气怎么样？",
    "推荐几只股票给我",
    "你的家庭住址在哪里？",
    "你的生日是哪天？",
    "解释一下量子纠缠的原理",
]

# Conservative first-cut threshold: hit rate must reach this; refine after real
# numbers come in (swap in a real embedding to compare).
_MIN_HIT_RATE = 0.75

# ---------------------------------------------------------------------------
# Shared harness (self-contained copy of the test_knowledge.py pattern)
# ---------------------------------------------------------------------------


def _reset_database(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users, knowledge_documents CASCADE"))


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
        engine.dispose()


def _seed_owner(engine: Engine) -> UUID:
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
                "role": "owner_admin",
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


def _upload(client: AsyncClient) -> Any:
    payload = [
        ("files", (name, content.encode("utf-8"), "text/markdown"))
        for name, content in CORPUS.items()
    ]
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


async def _stream_answer(client: AsyncClient, question: str) -> list[tuple[str, dict[str, object]]]:
    response = await client.post(
        "/answers:stream", json={"question": question, "page_key": "resume"}
    )
    assert response.status_code == 200
    return _events(response.text)


def _completed(events: list[tuple[str, dict[str, object]]]) -> dict[str, object]:
    for name, data in events:
        if name == "answer.completed":
            return data
    return {}


def _cited_docs(events: list[tuple[str, dict[str, object]]]) -> list[str]:
    for name, data in events:
        if name == "answer.citations":
            return [str(cite["doc"]) for cite in data.get("citations", [])]
    return []


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rag_hit_cases(real_stack: Any) -> None:
    """8 hit cases: grounded=True and the expected doc appears in citations."""
    engine, app, settings = real_stack
    owner = _seed_owner(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        response = await _upload(client)
        assert response.status_code == 202
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        assert {item["name"] for item in listed} == set(CORPUS)
        assert all(item["status"] == "indexed" for item in listed)

        passed = 0
        results: list[str] = []
        for question, expected_doc in HIT_CASES:
            events = await _stream_answer(client, question)
            completed = _completed(events)
            docs = _cited_docs(events)
            ok = bool(completed.get("grounded")) and expected_doc in docs
            passed += int(ok)
            results.append(
                f"  {'PASS' if ok else 'FAIL'} {question} -> docs={docs} "
                f"(want {expected_doc}) grounded={completed.get('grounded')}"
            )
        for line in results:
            print(line)
        print(f"== RAG HIT  = {passed}/{len(HIT_CASES)} ({passed / len(HIT_CASES):.0%})")
        assert passed / len(HIT_CASES) >= _MIN_HIT_RATE


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason=(
        "P1 known defect: hybrid retrieval has no relevance threshold, so vector "
        "top-k hard-recalls irrelevant questions -> grounded instead of refused. "
        "The evaluation makes reject rate measurable; add the threshold to turn green."
    ),
    strict=False,
)
async def test_rag_reject_cases(real_stack: Any) -> None:
    """6 reject cases must be refused (offtopic=True). xfail = measured defect."""
    engine, app, settings = real_stack
    owner = _seed_owner(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        response = await _upload(client)
        assert response.status_code == 202

        refused = 0
        results: list[str] = []
        for question in REJECT_CASES:
            events = await _stream_answer(client, question)
            completed = _completed(events)
            ok = bool(completed.get("offtopic"))
            refused += int(ok)
            results.append(
                f"  {'PASS' if ok else 'FAIL'} {question} -> "
                f"offtopic={completed.get('offtopic')} grounded={completed.get('grounded')}"
            )
        for line in results:
            print(line)
        print(f"== RAG REJECT= {refused}/{len(REJECT_CASES)} ({refused / len(REJECT_CASES):.0%})")
        assert refused == len(REJECT_CASES)
