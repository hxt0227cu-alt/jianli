"""Answer service orchestration (M6 rounds 1-3).

Pipeline: retrieve grounded chunks (knowledge base via pgvector when available, else the
static page registry) → boundary check (greeting / off-topic refusal, persona voice) →
stream model deltas through the LLM gateway → emit SSE frames exactly as docs/api/sse.md
§3 defines.

Round 2: conversation persistence over the approved 0004 tables — with a valid session
**and** a ``conversation_id`` the user question is stored before the stream and the
assistant answer (with its ``is_offtopic`` flag) afterwards; the ``answer.started`` frame
echoes that ``conversation_id``. Anonymous calls and logged-in calls without a
``conversation_id`` are never persisted.

Round 3: knowledge-base ingestion (md/txt, local-disk storage, pgvector embeddings).
Round 4 (TASK-KB-PDF-001): PDF uploads supported (pypdf text extraction, parse_mode=native)
so the resume PDF itself can be indexed; md/txt stay parse_mode=text; docx stays failed.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import re
import time
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict, cast
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.appointments.models import AppointmentDraft, AppointmentUpdate, Slot
from app.appointments.service import LOCAL_TIME, BookingService
from app.auth.errors import AuthError
from app.auth.models import Principal

from . import bm25
from .chunking import chunk_text as _chunk_text
from .content import PAGES, PageContentData, build_resume_facts_card
from .embeddings import EmbeddingError, EmbeddingGateway
from .gateway import GatewayError, LLMGateway
from .models import (
    Conversation,
    ConversationList,
    KnowledgeDocument,
    KnowledgeDocumentList,
    Message,
    MessageList,
    RecommendationSource,
)
from .persona import GREETING_REPLY, OFFTOPIC_REPLY, build_system_prompt, is_greeting
from .rate_limit import AnswerRateLimiter
from .repository import ConversationRepository, KnowledgeRepository, default_now
from .retrieval import Candidate, retrieve
from .sse import (
    booking_frame,
    citations_frame,
    completed_frame,
    delta_frame,
    error_frame,
    started_frame,
    tool_calls_frame,
)
from .storage import KnowledgeStorage

logger = logging.getLogger("jianli.aiqa")

_OFFTOPIC_CODE = "OFFTOPIC"
_GREETING_CODE = "GREETING"
_PRIVACY_CODE = "PRIVACY"
_MALICIOUS_CODE = "MALICIOUS"

# Privacy guard (TASK-AIQA-PRIVACY-GUARD-012): refuse PII / private-life questions
# directly, independent of retrieval score. The expanded real corpus contains
# location/GPA chunks that push some privacy queries (家庭住址 / 工资) just above
# the 0.47 relevance threshold, so a score-only gate is insufficient — the intent
# is refused explicitly. Matches the project's "隐私拦截" stance (no fabrication,
# no privacy leak from loosely-matched chunks).
_PRIVACY_REPLY = (
    "这个问题涉及我的个人隐私，我不太方便回答～"
    "你可以问我关于技术、项目或经历的问题，我很乐意聊那些。"
)
_PRIVACY_PATTERN = re.compile(
    r"(家庭住址|住址|家庭地址|老家|住在哪里|住在哪|"
    r"工资|薪资|收入|月薪|年薪|薪酬|年终奖|提成|月入|赚|挣|"
    r"身份证|手机号|电话号码|银行卡|社保|公积金|"
    r"私生活|私事|感情|男朋友|女朋友|结婚|老婆|老公|"
    r"生日|出生日期|几月几号出生|哪天出生)"
)


def _is_privacy_question(question: str) -> bool:
    return bool(_PRIVACY_PATTERN.search(question))


# Malicious-intent guard (TASK-AIQA-KB-DOMAIN-015): refuse harmful / illegal requests
# (hacking, forgery, theft, attacks on others' systems) directly, on the same
# deterministic layer as the privacy guard. The expanded corpus now contains wifi /
# OTA content that pushes "怎么破解邻居家的 wifi 密码" just above the 0.47 relevance
# threshold, so a score-only gate is insufficient — the intent is refused explicitly.
# The regex is applied to the *question only* (never to corpus text), so legitimate
# interview questions (which never contain these phrasings) are unaffected.
_MALICIOUS_REPLY = (
    "这类涉及非法或攻击性行为的问题，我没办法回答～"
    "如果你对网络安全防护、系统加固这些技术本身感兴趣，我很乐意聊聊。"
)
_MALICIOUS_PATTERN = re.compile(
    r"(黑进|越权访问|暴力破解|撞库|薅羊毛|"
    r"破解.{0,8}(密码|wifi|wifi 密码|系统|账号)|"
    r"(密码|账号|wifi).{0,4}(破解|入侵|盗)|"
    r"窃取|盗取|骗取|伪造|造假|"
    r"攻击.{0,4}(他人|别人|系统|网站|服务器|账户|账号)|"
    r"入侵.{0,4}(别人|他人|系统|电脑|服务器|账号|网站)|"
    r"黑进.{0,6}(系统|账号|电脑)|"
    r"爬虫.{0,10}(抓取|采集|爬取).{0,10}(微博|微信|淘宝|抖音|小红书|京东|评论区|帖子|账号|私信)|"
    r"(生成|制作|伪造|造假|编造|办一张|做一张|搞一张).{0,10}(病假条|请假条|诊断证明|病历|证明|证件|文凭|发票|毕业证|学位证|资格证))"
)
# Defensive-context exemption: "怎么防止别人入侵/破解/攻击" is a legitimate security
# question, not an attack request. Checked before the malicious pattern so defensive
# phrasings are never refused.
_DEFENSIVE_PREFIX = re.compile(
    r"(防止|防范|防御|防护|如何防|怎么防|安全防护|加固|拦截).{0,6}(入侵|攻击|破解|盗|黑客)"
)


def _is_malicious_question(question: str) -> bool:
    if _DEFENSIVE_PREFIX.search(question):
        return False
    return bool(_MALICIOUS_PATTERN.search(question))


# KB domain scoping (TASK-AIQA-KB-DOMAIN-015): the KB is one shared pgvector corpus
# across all pages, but each projects page must only retrieve its own documents —
# otherwise a jianli question pulls Taiyizhi/Litchi chunks (observed 2026-08-18:
# FQ-13 answered NestJS/115REST/35 表, FQ-24 answered the thesis load-test, FQ-27
# answered Python+FastAPI for a Spring Boot project). Mapping:
#   resume                  -> None (any experience topic may be asked on the resume page)
#   projects / jianli       -> []  (jianli facts live in static pages only)
#   projects / litchi       -> ["litchi.md"]
#   projects / sleep202603_an -> ["taiyizhi.md"]
#   projects / (none)       -> None (competition / behavioural questions)
# None = unrestricted (legacy behaviour); [] = no KB docs for this domain.
def _kb_domain_docs(page_key: str, project_key: str | None) -> list[str] | None:
    if page_key == "projects":
        if project_key == "jianli":
            return []
        if project_key == "litchi":
            return ["litchi.md"]
        if project_key == "sleep202603_an":
            return ["taiyizhi.md"]
    return None
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # openapi KnowledgeDocument.size maximum 10485760
_SUPPORTED_TYPES = {"md", "txt", "pdf"}
# Multi-turn memory backfill (TASK-M6-HARDENING-001): inject at most this many of the most
# recent prior messages as context. Bounded to keep the prompt from inflating; long
# transcripts would need summarisation, which is deliberately out of scope for now.
_MAX_HISTORY_MESSAGES = 6

# Agent tooling (TASK-AGENT-TOOLS-002): the single whitelisted read-only tool. The model
# decides whether to call it and generates its own `query` (tool_choice=auto); the service
# executes it with the existing hybrid retrieval. Booking/write/admin endpoints are never
# registered here (PRD decision #14) — see docs/api/sse.md §3.
_SEARCH_TOOLS: list[dict[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "在站点主人的公开知识库（简历、项目、技术笔记等资料）中检索与用户问题"
                "相关的片段。当问题需要事实依据时调用；请用问题中的关键主题词作为检索词"
                "query（如项目名、技术名、经历关键词），不要整句复制问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "检索词：问题中的关键主题词，例如 'Litchi Copilot'、"
                            "'技术栈'、'腾讯实习'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# Autonomous interview booking (TASK-AIQA-BOOKING-001): a write tool the model may call
# when the interviewer explicitly wants to book a slot. The service executes it in-process
# with the caller's principal (RBAC enforced inside `_run_booking_tool`, because
# `BookingService` itself does not re-check role). Only `target_date` + `start_time` are
# required; business fields the natural language cannot carry are optional and trigger a
# `needs_info` follow-up rather than silent defaults (keeps AppointmentDraft validation
# and the appointments domain untouched). Duration is fixed at 90 min (3 × 30-min slots);
# the model supplies only the start time.
_BOOKING_TOOL: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "request_interview_booking",
        "description": (
            "当面试官/访客明确想预约面试时间时调用（例如「我想预约下周三下午两点的面试」）。"
            "请解析出本地日期(target_date, YYYY-MM-DD)与开始时间(start_time, HH:MM, 24小时制)："
            "「下周三」要相对今天按 Asia/Shanghai 推算具体日期，「下午两点」即 14:00。"
            "每次面试固定 90 分钟（3 个连续时段），只需给起点。若用户未提供公司名、面试平台、"
            "会议号或联系人信息，这些字段可省略（系统会随后追问），不要用猜测值填充。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "本地日期 YYYY-MM-DD（「下周三」相对今天按 Asia/Shanghai 推算）",
                },
                "start_time": {
                    "type": "string",
                    "description": "本地开始时间 HH:MM，24小时制，如「14:00」",
                },
                "company_name": {"type": "string", "description": "公司/团队名称，用户提供才填"},
                "meeting_platform": {
                    "type": "string",
                    "description": "面试平台，如 腾讯会议/飞书/Zoom，用户提供才填",
                },
                "meeting_number": {"type": "string", "description": "会议号，用户提供才填"},
                "contact_last_name": {"type": "string", "description": "联系人姓，用户提供才填"},
                "contact_salutation": {
                    "type": "string",
                    "description": "称谓，如 先生/女士/同学，用户提供才填",
                },
                "contact_phone": {"type": "string", "description": "联系电话，用户提供才填"},
            },
            "required": ["target_date", "start_time"],
        },
    },
}

# Interview self-service tools (TASK-AIQA-AGENT-CRUD-001): let the model list/cancel/
# reschedule appointments through a multi-step loop. interviewers act on their own rows
# only; owner_admin sees/manages every appointment.
_LIST_TOOL: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "list_my_appointments",
        "description": (
            "列出当前登录账号名下的面试预约（时间、公司、状态等）。"
            "在想取消或改期某条预约前，先调用本工具拿到要操作的 appointment_id。"
            "若当前账号是站长(owner)，则返回系统中全部预约（含他人）。"
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

_CANCEL_TOOL: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "cancel_appointment",
        "description": (
            "取消一条面试预约（需先经 list_my_appointments 拿到 appointment_id）。"
            "面试官只能取消自己名下的预约；站长可取消任意预约。取消后该时段释放。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "要取消的预约 id（来自 list_my_appointments 的 appointment_id）",
                },
            },
            "required": ["appointment_id"],
        },
    },
}

_RESCHEDULE_TOOL: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "reschedule_appointment",
        "description": (
            "改期一条面试预约到新的开始时间（需先经 list_my_appointments 拿到 appointment_id）。"
            "面试官只能改自己名下的预约；站长可改任意预约。每次面试固定 90 分钟（3 个连续时段）。"
            "「下周三」要相对今天按 Asia/Shanghai 推算具体日期。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "要改期的预约 id（来自 list_my_appointments 的 appointment_id）",
                },
                "target_date": {
                    "type": "string",
                    "description": "新日期 YYYY-MM-DD（「下周三」按 Asia/Shanghai 推算）",
                },
                "start_time": {
                    "type": "string",
                    "description": "新的本地开始时间 HH:MM，24小时制，如「10:00」",
                },
            },
            "required": ["appointment_id", "target_date", "start_time"],
        },
    },
}

# All tools are offered with tool_choice=auto; the model picks search_knowledge for
# factual Q&A, request_interview_booking for an explicit booking intent, and the
# self-service tools (list/cancel/reschedule) to manage existing appointments.
_AGENT_TOOLS: list[dict[str, object]] = [
    *_SEARCH_TOOLS,
    _BOOKING_TOOL,
    _LIST_TOOL,
    _CANCEL_TOOL,
    _RESCHEDULE_TOOL,
]


def _extract_pdf_text(raw: bytes) -> str:
    """Extract text from a PDF via pypdf (TASK-KB-PDF-001)."""

    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ValueError("pypdf is required for PDF parsing") from error
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _format_context(candidates: list[Candidate]) -> str:
    return "\n".join(f"[{c.doc} #{c.fragment}] {c.text}" for c in candidates)


def _add_usage(acc: dict[str, int], payload: dict[str, object]) -> None:
    """Accumulate token usage across streaming phases (Phase1 tool-decision + Phase2 answer)."""
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = payload.get(key)
        if isinstance(value, int):
            acc[key] += value


class _ToolTraceEntry(TypedDict):
    name: str
    result: dict[str, Any]


def _conversation_from(row: dict[str, Any]) -> Conversation:
    return Conversation(
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _message_from(row: dict[str, Any]) -> Message:
    return Message(
        id=row["id"],
        role=row["role"],
        content=row["content"],
        is_offtopic=row["is_offtopic"],
        created_at=row["created_at"],
    )


class AnswerService:
    """Per-request orchestration; holds the gateway, rate limiter and optional stores."""

    def __init__(
        self,
        gateway: LLMGateway,
        rate_limiter: AnswerRateLimiter,
        repository: ConversationRepository | None = None,
        embedder: EmbeddingGateway | None = None,
        knowledge_repository: KnowledgeRepository | None = None,
        storage: KnowledgeStorage | None = None,
        min_score: float = 0.0,
        booking_service: BookingService | None = None,
    ) -> None:
        self._gateway = gateway
        self._rate_limiter = rate_limiter
        self._repository = repository
        self._embedder = embedder
        self._knowledge_repository = knowledge_repository
        self._storage = storage
        self._min_score = min_score
        # Autonomous booking (TASK-AIQA-BOOKING-001): injected from the appointments
        # runtime so the agent can call BookingService.preview/create in-process. None
        # when booking is not configured -> booking tool yields a graceful "unavailable".
        self._booking_service = booking_service

    # -- synchronous helpers used by the router before streaming -------------------------

    def check_rate_limit(self, ip: str) -> None:
        """Public answer rate limit; raises AuthError 429 on budget exhaustion."""

        self._rate_limiter.consume(ip)

    def page_content(self, page_key: str) -> PageContentData | None:
        return PAGES.get(page_key)

    def recommendations(self, page_key: str) -> tuple[list[str], RecommendationSource]:
        page = PAGES.get(page_key)
        if page is None:
            return [], "fallback"
        return page.recommendations, "fallback"

    # -- conversation endpoints (round 2) -------------------------------------------------

    def _require_repository(self) -> ConversationRepository:
        if self._repository is None:
            raise AuthError(
                "MODEL_UNAVAILABLE", 503, "Conversation storage unavailable", "Retry later"
            )
        return self._repository

    def list_conversations(self, user_id: UUID) -> ConversationList:
        repository = self._require_repository()
        rows = repository.list_conversations(user_id)
        return ConversationList(items=[_conversation_from(row) for row in rows])

    def create_conversation(self, user_id: UUID) -> Conversation:
        repository = self._require_repository()
        row = repository.create_conversation(user_id, default_now())
        return _conversation_from(row)

    def list_messages(self, user_id: UUID, conversation_id: UUID) -> MessageList:
        repository = self._require_repository()
        conversation = repository.get_conversation(conversation_id)
        if conversation is None or conversation.get("deleted_at") is not None:
            raise AuthError(
                "INVALID_REQUEST", 404, "Conversation not found", "Unknown conversation"
            )
        if conversation["user_id"] != user_id:
            raise AuthError(
                "PERM_DENIED", 403, "Forbidden", "Conversation belongs to another user"
            )
        rows = repository.list_messages(conversation_id)
        return MessageList(items=[_message_from(row) for row in rows])

    # -- knowledge-base endpoints (round 3) -----------------------------------------------

    def _require_knowledge(self) -> tuple[KnowledgeRepository, KnowledgeStorage, EmbeddingGateway]:
        if self._knowledge_repository is None or self._storage is None or self._embedder is None:
            raise AuthError("MODEL_UNAVAILABLE", 503, "Knowledge base unavailable", "Retry later")
        return self._knowledge_repository, self._storage, self._embedder

    def list_knowledge_documents(self) -> KnowledgeDocumentList:
        repository, _, _ = self._require_knowledge()
        items: list[KnowledgeDocument] = []
        for row in repository.list_documents():
            items.append(
                KnowledgeDocument(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    size=row["size"],
                    status=row["status"],
                    parse_mode=row.get("parse_mode"),
                    failure_reason=row.get("failure_reason"),
                    created_at=row["created_at"],
                )
            )
        return KnowledgeDocumentList(items=items)

    async def upload_knowledge_documents(self, files: Sequence[Any]) -> None:
        """Parse + index each md/txt/pdf upload (202 semantics; per-file status in list)."""

        repository, storage, embedder = self._require_knowledge()
        now = default_now()
        for file in files:
            filename = (file.filename or "document").rsplit("/", 1)[-1]
            suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if suffix not in {"md", "pdf", "docx", "txt"}:
                continue  # unknown extension: nothing to index
            document_id = uuid4()
            try:
                raw = await file.read()
            except Exception:  # pragma: no cover - defensive
                continue
            checksum = hashlib.sha256(raw).hexdigest()
            try:
                repository.create_document(
                    document_id=document_id,
                    name=filename,
                    doc_type=suffix,
                    size=len(raw),
                    content_checksum=checksum,
                    storage_key=f"knowledge/{document_id}.txt",
                    parse_mode="native" if suffix == "pdf" else "text",
                    now=now,
                )
            except IntegrityError:
                continue  # active checksum duplicate (uq_knowledge_documents_active_checksum)
            if len(raw) > _MAX_UPLOAD_BYTES:
                await asyncio.to_thread(
                    repository.mark_failed, document_id, "file exceeds 10MB limit"
                )
                continue
            if suffix not in _SUPPORTED_TYPES:
                await asyncio.to_thread(
                    repository.mark_failed, document_id, f"{suffix} parsing is not supported in MVP"
                )
                continue
            if suffix == "pdf":
                try:
                    text = await asyncio.to_thread(_extract_pdf_text, raw)
                except Exception as error:  # pypdf failure or corrupt PDF -> failed with reason
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, f"PDF parse failed: {error}"
                    )
                    continue
                if not text.strip():
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, "no extractable text in PDF"
                    )
                    continue
            else:
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, "not valid UTF-8 text"
                    )
                    continue
            storage.save(document_id, text)
            try:
                chunks = _chunk_text(text)
                chunk_texts = [content for _, content in chunks]
                embeddings = embedder.embed(chunk_texts)
            except EmbeddingError as error:
                await asyncio.to_thread(repository.mark_failed, document_id, str(error))
                continue
            await asyncio.to_thread(
                repository.replace_chunks, document_id, chunks, embeddings, default_now()
            )
            await asyncio.to_thread(repository.mark_indexed, document_id)

    def delete_knowledge_document(self, document_id: UUID) -> None:
        repository, storage, _ = self._require_knowledge()
        document = repository.get_document(document_id)
        if document is None:
            raise AuthError("INVALID_REQUEST", 404, "Document not found", "Unknown document")
        repository.disable_retrieval(document_id, default_now())
        storage.delete(document_id)

    # -- streaming pipeline ---------------------------------------------------------------

    # -- autonomous booking (TASK-AIQA-BOOKING-001) ------------------------------------------

    def _require_booking(self) -> BookingService:
        if self._booking_service is None:
            raise AuthError(
                "BOOKING_UNAVAILABLE", 503, "Booking unavailable", "Retry later"
            )
        return self._booking_service

    @staticmethod
    def _as_str(value: object) -> str:
        return value if isinstance(value, str) else ""

    @staticmethod
    def _to_local(value: datetime) -> datetime:
        """Normalise a slot start_at (UTC-aware or naive UTC from the DB) to Asia/Shanghai."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(LOCAL_TIME)

    def _resolve_booking_slots(
        self, booking: BookingService, principal: Principal, start_local: datetime
    ) -> list[Slot] | None:
        """Resolve the 3 consecutive available 30-min slots starting at ``start_local``.

        Reuses ``BookingService.slot_snapshot`` (no new appointments-domain method) by
        locating the week containing ``start_local`` and filtering the three needed local
        start times. Returns None if any of the three is missing or not ``available``.
        """
        today = datetime.now(UTC).astimezone(LOCAL_TIME).date()
        today_monday = today - timedelta(days=today.weekday())
        target_monday = start_local.date() - timedelta(days=start_local.weekday())
        week_offset = (target_monday - today_monday).days // 7
        snapshot = booking.slot_snapshot(principal, week_offset)
        needed = [
            self._to_local(start_local + timedelta(minutes=30 * i)) for i in range(3)
        ]
        by_local_start = {self._to_local(slot.start_at): slot for slot in snapshot.items}
        resolved: list[Slot] = []
        for when in needed:
            slot = by_local_start.get(when)
            if slot is None or slot.status != "available":
                return None
            resolved.append(slot)
        return resolved

    async def _run_booking_tool(
        self, arguments: dict[str, object], principal: Principal | None
    ) -> dict[str, object]:
        """Execute the ``request_interview_booking`` tool in-process.

        Returns a structured outcome dict consumed by ``stream_answer`` -> ``booking_frame``.
        The appointments domain's strong invariants (3x30min consecutive, same local day,
        token two-phase, row lock, company fingerprint dedupe) are all reused via
        ``BookingService.preview/create`` — this method only adds RBAC, natural-language
        slot resolution and business-field completeness checks.
        """
        # RBAC: the in-process call bypasses the router's require_role, and BookingService
        # does not re-check role, so we must enforce it here.
        if principal is None or getattr(principal, "role", None) != "interviewer":
            return {
                "outcome": "forbidden",
                "payload": {"reason": "请先以面试官账号登录后再预约面试。"},
            }

        target_date = self._as_str(arguments.get("target_date"))
        start_time = self._as_str(arguments.get("start_time"))
        try:
            day = datetime.strptime(target_date, "%Y-%m-%d").date()
            hh, mm = (int(part) for part in start_time.split(":"))
            start_local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=LOCAL_TIME)
        except (ValueError, TypeError, AttributeError):
            return {
                "outcome": "needs_info",
                "payload": {
                    "missing": ["target_date", "start_time"],
                    "reason": "请明确预约的日期与开始时间，例如「下周三下午两点」。",
                },
            }

        booking = self._require_booking()
        slots = await asyncio.to_thread(
            self._resolve_booking_slots, booking, principal, start_local
        )
        if slots is None:
            return {
                "outcome": "failed",
                "payload": {
                    "reason": "该时段未开放或已被预约；可在「预约」页查看可约时间。",
                },
            }

        company = self._as_str(arguments.get("company_name"))
        platform = self._as_str(arguments.get("meeting_platform"))
        number = self._as_str(arguments.get("meeting_number"))
        last = self._as_str(arguments.get("contact_last_name"))
        salutation = self._as_str(arguments.get("contact_salutation"))
        phone = self._as_str(arguments.get("contact_phone"))
        missing = [
            name
            for name, value in (
                ("company_name", company),
                ("meeting_platform", platform),
                ("meeting_number", number),
                ("contact_last_name", last),
                ("contact_salutation", salutation),
                ("contact_phone", phone),
            )
            if not value
        ]
        if missing:
            return {"outcome": "needs_info", "payload": {"missing": missing}}

        draft = AppointmentDraft(
            slot_ids=[slot.id for slot in slots],
            company_name=company,
            meeting_platform=platform,
            meeting_number=number,
            contact_last_name=last,
            contact_salutation=salutation,
            contact_phone=phone,
        )
        try:
            preview_result = await asyncio.to_thread(booking.preview, principal, draft)
            appointment = await asyncio.to_thread(
                booking.create, principal, draft, preview_result.confirmation_token
            )
        except AuthError as error:
            detail = error.detail
            reason = detail if isinstance(detail, str) else "预约失败，请稍后重试。"
            return {"outcome": "failed", "payload": {"reason": reason}}
        except IntegrityError:
            return {
                "outcome": "failed",
                "payload": {
                    "reason": "预约冲突或服务繁忙，请稍后再试或在「预约」页手动预约。",
                },
            }

        return {
            "outcome": "confirmed",
            "payload": {
                "appointment_id": str(appointment.id),
                "start_at": appointment.start_at.isoformat(),
                "end_at": appointment.end_at.isoformat(),
                "company_name": appointment.company_name,
                "meeting_platform": appointment.meeting_platform,
                "contact": (
                    f"{appointment.contact_salutation}{appointment.contact_last_name} "
                    f"{appointment.contact_phone}"
                ),
            },
        }

    async def _run_agent_tool(
        self, name: str, arguments: dict[str, object], principal: Principal | None
    ) -> dict[str, object]:
        """Dispatch a whitelisted agent tool (TASK-AIQA-AGENT-CRUD-001).

        Central RBAC: every tool except ``search_knowledge`` requires an authenticated
        principal. ``BookingService`` trusts the principal and does NOT re-check role, so
        the per-tool role enforcement here is the single authority for agent-invoked
        writes. ``search_knowledge`` returns a signal dict consumed by the loop, not a
        booking-style outcome.
        """

        if name == "search_knowledge":
            return {"outcome": "search", "payload": {"query": str(arguments.get("query") or "")}}

        # All remaining tools require an authenticated caller.
        if principal is None:
            return {
                "outcome": "forbidden",
                "payload": {"reason": "请先以面试官账号登录后再操作预约。"},
            }

        if name == "request_interview_booking":
            return await self._run_booking_tool(arguments, principal)
        if name == "list_my_appointments":
            return self._run_list_tool(principal)
        if name == "cancel_appointment":
            return await self._run_cancel_tool(arguments, principal)
        if name == "reschedule_appointment":
            return await self._run_reschedule_tool(arguments, principal)
        return {"outcome": "failed", "payload": {"reason": "未支持的工具调用。"}}

    def _run_list_tool(self, principal: Principal) -> dict[str, object]:
        """List appointments for the caller (TASK-AIQA-AGENT-CRUD-001).

        owner_admin gets every appointment (incl. others) via ``admin_list_appointments``;
        everyone else gets only their own active rows via ``list_my``.
        """

        booking = self._require_booking()
        is_owner = getattr(principal, "role", None) == "owner_admin"
        try:
            rows = (
                booking.admin_list_appointments()
                if is_owner
                else booking.list_my(principal)
            )
        except AuthError as error:
            detail = error.detail
            reason = detail if isinstance(detail, str) else "查询失败，请稍后重试。"
            return {"outcome": "failed", "payload": {"reason": reason}}
        items = [
            {
                "appointment_id": str(row.id),
                "start_at_local": self._to_local(row.start_at).isoformat(),
                "end_at_local": self._to_local(row.end_at).isoformat(),
                "company_name": row.company_name,
                "status": row.status,
                "version": row.version,
            }
            for row in rows
        ]
        return {
            "outcome": "listed",
            "payload": {"items": items, "scope": "all" if is_owner else "mine"},
        }

    async def _run_cancel_tool(
        self, arguments: dict[str, object], principal: Principal
    ) -> dict[str, object]:
        """Cancel an appointment (TASK-AIQA-AGENT-CRUD-001).

        owner_admin uses the ownership-bypassing ``force_cancel``; others use ``cancel``
        which enforces ownership via ``_load_owned_for_write`` (non-owner → PERM_DENIED).
        """

        booking = self._require_booking()
        aid_raw = self._as_str(arguments.get("appointment_id"))
        try:
            aid = UUID(aid_raw)
        except (ValueError, AttributeError):
            return {"outcome": "failed", "payload": {"reason": "预约 id 格式不正确。"}}
        is_owner = getattr(principal, "role", None) == "owner_admin"
        try:
            if is_owner:
                await asyncio.to_thread(booking.force_cancel, principal, aid)
            else:
                await asyncio.to_thread(booking.cancel, principal, aid)
        except AuthError as error:
            return self._map_write_error(error, "取消")
        return {"outcome": "cancelled", "payload": {"appointment_id": str(aid)}}

    async def _run_reschedule_tool(
        self, arguments: dict[str, object], principal: Principal
    ) -> dict[str, object]:
        """Reschedule an appointment to a natural-language time (TASK-AIQA-AGENT-CRUD-001).

        Reuses ``_resolve_booking_slots`` for 3 consecutive available slots. owner_admin
        bypasses ownership via ``admin_reschedule``; others read their own version then
        call ``update`` (which re-checks ownership and the optimistic-lock version).
        """

        booking = self._require_booking()
        aid_raw = self._as_str(arguments.get("appointment_id"))
        target_date = self._as_str(arguments.get("target_date"))
        start_time = self._as_str(arguments.get("start_time"))
        try:
            aid = UUID(aid_raw)
            day = datetime.strptime(target_date, "%Y-%m-%d").date()
            hh, mm = (int(part) for part in start_time.split(":"))
            start_local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=LOCAL_TIME)
        except (ValueError, TypeError, AttributeError):
            return {
                "outcome": "needs_info",
                "payload": {
                    "missing": ["target_date", "start_time"],
                    "reason": "请明确新的日期与开始时间，例如「8月25日上午10点」。",
                },
            }
        slots = await asyncio.to_thread(
            self._resolve_booking_slots, booking, principal, start_local
        )
        if slots is None:
            return {
                "outcome": "failed",
                "payload": {"reason": "该时段未开放或已被预约；可在「预约」页查看可约时间。"},
            }
        slot_ids = [slot.id for slot in slots]
        is_owner = getattr(principal, "role", None) == "owner_admin"
        try:
            if is_owner:
                await asyncio.to_thread(booking.admin_reschedule, principal, aid, slot_ids)
            else:
                own = await asyncio.to_thread(booking.read_own, principal, aid)
                await asyncio.to_thread(
                    booking.update,
                    principal,
                    aid,
                    AppointmentUpdate(version=own.version, new_slot_ids=slot_ids),
                )
        except AuthError as error:
            return self._map_write_error(error, "改期")
        return {
            "outcome": "rescheduled",
            "payload": {
                "appointment_id": str(aid),
                "start_at_local": self._to_local(slots[0].start_at).isoformat(),
                "end_at_local": self._to_local(slots[-1].end_at).isoformat(),
            },
        }

    @staticmethod
    def _map_write_error(error: AuthError, verb: str) -> dict[str, object]:
        """Map a BookingService AuthError to a graceful agent outcome (CRUD-001)."""

        detail = error.detail
        reason = detail if isinstance(detail, str) else f"{verb}失败，请稍后重试。"
        code = error.code
        if code == "PERM_DENIED":
            return {
                "outcome": "forbidden",
                "payload": {"reason": f"这不是你名下的预约，无法{verb}。"},
            }
        if code == "NOT_FOUND":
            return {"outcome": "not_found", "payload": {"reason": "未找到该预约，可能已被取消。"}}
        if code == "TERMINAL_STATE":
            return {"outcome": "terminal", "payload": {"reason": f"该预约已结束，无法{verb}。"}}
        if code == "VERSION_CONFLICT":
            return {
                "outcome": "conflict",
                "payload": {"reason": "预约信息已变化，请重新查询后再改期。"},
            }
        return {"outcome": "failed", "payload": {"reason": reason}}

    async def stream_answer(
        self,
        *,
        question: str,
        page_key: str,
        project_key: str | None,
        principal: Principal | None,
        conversation_id: UUID | None,
    ) -> AsyncIterator[str]:
        """Yield SSE frames for one answer (started → deltas → citations → completed)."""

        persist = (
            principal is not None
            and conversation_id is not None
            and self._repository is not None
        )
        trace_id = str(uuid4())
        start = time.monotonic()
        history: list[dict[str, str]] = []
        seq = 0
        answer_id = str(uuid4())
        yield started_frame(
            seq := seq + 1,
            answer_id,
            str(conversation_id) if persist else None,
            trace_id,
        )

        if persist:
            assert (
                principal is not None
                and conversation_id is not None
                and self._repository is not None
            )
            history = await self._load_history(conversation_id)
            await asyncio.to_thread(
                self._repository.append_message,
                conversation_id,
                role="user",
                content=question,
                is_offtopic=False,
                now=default_now(),
            )

        deltas: list[str] = []

        # Greeting first (no model round-trip, unchanged policy).
        if is_greeting(question):
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "answer_greeting",
                extra={
                    "trace_id": trace_id,
                    "conversation_id": str(conversation_id) if persist else None,
                    "grounded": False,
                    "offtopic": False,
                    "model": _GREETING_CODE,
                    "latency_ms": latency_ms,
                },
            )
            yield delta_frame(seq := seq + 1, GREETING_REPLY, trace_id)
            yield citations_frame(seq := seq + 1, [], trace_id)
            yield completed_frame(
                seq := seq + 1,
                grounded=False,
                offtopic=False,
                model=_GREETING_CODE,
                usage=None,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, GREETING_REPLY, False)
            return

        # Privacy guard (TASK-AIQA-PRIVACY-GUARD-012): refuse PII / private-life questions
        # directly, before any model round-trip or retrieval. The score-only off-topic
        # gate is insufficient once the real corpus contains location/GPA chunks that
        # make privacy queries score just above the 0.47 threshold.
        if _is_privacy_question(question):
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "answer_privacy",
                extra={
                    "trace_id": trace_id,
                    "conversation_id": str(conversation_id) if persist else None,
                    "grounded": False,
                    "offtopic": True,
                    "model": _PRIVACY_CODE,
                    "latency_ms": latency_ms,
                },
            )
            yield delta_frame(seq := seq + 1, _PRIVACY_REPLY, trace_id)
            yield citations_frame(seq := seq + 1, [], trace_id)
            yield completed_frame(
                seq := seq + 1,
                grounded=False,
                offtopic=True,
                model=_PRIVACY_CODE,
                usage=None,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, _PRIVACY_REPLY, True)
            return

        # Malicious-intent guard (TASK-AIQA-KB-DOMAIN-015): refuse harmful / illegal
        # requests before any model round-trip, same deterministic layer as privacy.
        if _is_malicious_question(question):
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "answer_malicious",
                extra={
                    "trace_id": trace_id,
                    "conversation_id": str(conversation_id) if persist else None,
                    "grounded": False,
                    "offtopic": True,
                    "model": _MALICIOUS_CODE,
                    "latency_ms": latency_ms,
                },
            )
            yield delta_frame(seq := seq + 1, _MALICIOUS_REPLY, trace_id)
            yield citations_frame(seq := seq + 1, [], trace_id)
            yield completed_frame(
                seq := seq + 1,
                grounded=False,
                offtopic=True,
                model=_MALICIOUS_CODE,
                usage=None,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, _MALICIOUS_REPLY, True)
            return

        # Agent tooling (TASK-AGENT-TOOLS-002): two-phase function calling. Phase 1 —
        # the model decides whether to call the whitelisted read-only `search_knowledge`
        # tool and generates its own retrieval terms (`tool_choice=auto`). The service
        # executes the tool, then Phase 2 generates the grounded answer with the results.
        # No-hits always falls back to the existing off-topic refusal (never fabricate).
        _MODEL_ERROR_FRAME: dict[str, object] = {
            "type": "urn:jianli:error:model_unavailable",
            "title": "Model unavailable",
            "status": 503,
            "code": "MODEL_UNAVAILABLE",
            "detail": "The answer service is temporarily unavailable",
        }
        # ===== multi-step agent tool loop (TASK-AIQA-AGENT-CRUD-001) =====
        # The model may chain tools across turns (e.g. list_my_appointments →
        # cancel_appointment). Each step appends the tool result as an assistant message
        # (synthetic feedback; no dependency on the gateway's native tool-message protocol),
        # so the next model call sees prior outcomes. ``search_knowledge`` breaks the loop
        # into the RAG branch; a direct answer (no tool) breaks into the RAG fallback on
        # the original question. Bounded by MAX_STEPS to keep latency/P95 stable.
        agent_messages = [
            {"role": "system", "content": build_system_prompt()},
            *history,
            {"role": "user", "content": f"用户问题：{question}"},
        ]
        tool_trace: list[_ToolTraceEntry] = []
        search_query: str | None = None
        usage_acc = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        MAX_STEPS = 4
        try:
            for _ in range(MAX_STEPS):
                tool_request = None
                async for kind, payload in self._gateway.answer(agent_messages, tools=_AGENT_TOOLS):
                    if kind == "usage" and isinstance(payload, dict):
                        _add_usage(usage_acc, payload)
                        continue
                    if kind == "tool_call" and isinstance(payload, dict) and tool_request is None:
                        tool_request = payload
                        continue
                if tool_request is None:
                    break  # model answered directly (no tool)
                name = str(tool_request.get("name") or "")
                try:
                    args = json.loads(str(tool_request.get("arguments") or "{}"))
                except json.JSONDecodeError:
                    args = {}
                if name == "search_knowledge":
                    search_query = str(args.get("query") or question).strip() or question
                    break  # → RAG branch
                result = await self._run_agent_tool(name, args, principal)
                tool_trace.append({"name": name, "result": result})
                agent_messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"已调用工具 {name}，结果："
                            f"{json.dumps(result, ensure_ascii=False)}"
                        ),
                    }
                )
        except GatewayError as error:
            self._log_error(trace_id, conversation_id if persist else None, error)
            yield error_frame(seq := seq + 1, _MODEL_ERROR_FRAME, trace_id)
            return

        # ===== post-loop dispatch =====
        if search_query is not None or not tool_trace:
            # RAG branch (existing behavior preserved): search + grounded answer, or
            # off-topic refusal when there are no hits.
            candidates = await self._search_candidates(
                search_query or question, question, page_key, project_key
            )
            if not candidates:
                self._log_offtopic(trace_id, conversation_id if persist else None, start)
                yield tool_calls_frame(
                    seq := seq + 1,
                    [
                        {
                            "name": "search_knowledge",
                            "query": search_query or question,
                            "hits": [],
                        }
                    ],
                    trace_id,
                )
                yield delta_frame(seq := seq + 1, OFFTOPIC_REPLY, trace_id)
                yield citations_frame(seq := seq + 1, [], trace_id)
                yield completed_frame(
                    seq := seq + 1,
                    grounded=False,
                    offtopic=True,
                    model=_OFFTOPIC_CODE,
                    usage=None,
                    trace_id=trace_id,
                )
                if persist:
                    assert conversation_id is not None
                    await self._persist_assistant(conversation_id, OFFTOPIC_REPLY, True)
                return

            yield tool_calls_frame(
                seq := seq + 1,
                [
                    {
                        "name": "search_knowledge",
                        "query": search_query or question,
                        "hits": [{"doc": c.doc, "fragment": c.fragment} for c in candidates],
                    }
                ],
                trace_id,
            )
            messages2 = [
                {
                    "role": "system",
                    "content": build_system_prompt(
                        build_resume_facts_card() if page_key == "resume" else None
                    ),
                },
                *history,
                {
                    "role": "user",
                    "content": (
                        f"用户问题：{question}\n\n【已知资料】\n"
                        f"{_format_context(candidates)}"
                    ),
                },
            ]
            try:
                async for kind, payload in self._gateway.answer(messages2):
                    if kind == "usage" and isinstance(payload, dict):
                        _add_usage(usage_acc, payload)
                        continue
                    if kind != "delta" or not isinstance(payload, str):
                        continue
                    deltas.append(payload)
                    yield delta_frame(seq := seq + 1, payload, trace_id)
            except GatewayError as error:
                self._log_error(trace_id, conversation_id if persist else None, error)
                yield error_frame(seq := seq + 1, _MODEL_ERROR_FRAME, trace_id)
                return
            yield citations_frame(
                seq := seq + 1,
                [{"doc": c.doc, "fragment": c.fragment} for c in candidates],
                trace_id,
            )
            usage_payload = (
                cast("dict[str, object] | None", usage_acc)
                if usage_acc["total_tokens"] > 0
                else None
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "answer_completed",
                extra={
                    "trace_id": trace_id,
                    "conversation_id": str(conversation_id) if persist else None,
                    "grounded": True,
                    "offtopic": False,
                    "model": self._gateway.model_name,
                    "latency_ms": latency_ms,
                    "prompt_tokens": usage_acc["prompt_tokens"],
                    "completion_tokens": usage_acc["completion_tokens"],
                },
            )
            yield completed_frame(
                seq := seq + 1,
                grounded=True,
                offtopic=False,
                model=self._gateway.model_name,
                usage=usage_payload,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, "".join(deltas), False)
            return

        # ===== tool branch (booking / list / cancel / reschedule) =====
        # Emit a booking frame for each write-like outcome so the UI shows the
        # confirmation/cancel/reschedule card, then phrase the combined result naturally.
        for t in tool_trace:
            if t["name"] in (
                "request_interview_booking",
                "cancel_appointment",
                "reschedule_appointment",
            ):
                r = t["result"]
                yield booking_frame(seq := seq + 1, r["outcome"], r["payload"], trace_id)
        combined = "\n\n".join(
            f"【工具 {t['name']} 执行结果】\n{json.dumps(t['result'], ensure_ascii=False)}"
            for t in tool_trace
        )
        messages2 = [
            {"role": "system", "content": build_system_prompt()},
            *history,
            {
                "role": "user",
                "content": (
                    f"用户问题：{question}\n\n{combined}\n\n"
                    "请用自然、口语化的中文把以上操作结果一并向用户说明："
                    "若是「列出预约」，请逐条罗列每条的时间（本地时间）、公司、状态，"
                    "并附上 appointment_id 方便后续操作；"
                    "若是取消成功，请简要确认已取消；若是改期成功，请确认新时间；"
                    "若信息不全/未登录/非本人/时段不可用，请按工具给出的原因友好说明。"
                    "不要编造工具未返回的信息。"
                ),
            },
        ]
        try:
            async for kind, payload in self._gateway.answer(messages2):
                if kind == "usage" and isinstance(payload, dict):
                    _add_usage(usage_acc, payload)
                    continue
                if kind != "delta" or not isinstance(payload, str):
                    continue
                deltas.append(payload)
                yield delta_frame(seq := seq + 1, payload, trace_id)
        except GatewayError as error:
            self._log_error(trace_id, conversation_id if persist else None, error)
            yield error_frame(seq := seq + 1, _MODEL_ERROR_FRAME, trace_id)
            return
        usage_payload = (
            cast("dict[str, object] | None", usage_acc)
            if usage_acc["total_tokens"] > 0
            else None
        )
        yield completed_frame(
            seq := seq + 1,
            grounded=False,
            offtopic=False,
            model=self._gateway.model_name,
            usage=usage_payload,
            trace_id=trace_id,
        )
        if persist:
            assert conversation_id is not None
            await self._persist_assistant(conversation_id, "".join(deltas), False)
        return

    async def _search_candidates(
        self,
        primary: str,
        fallback: str,
        page_key: str,
        project_key: str | None,
    ) -> list[Candidate]:
        """Dual-path recall for the agent tool (TASK-AGENT-TOOLS-002).

        ``primary`` is the model-generated query from the tool call; ``fallback`` is the
        raw question. Both are searched (KB hybrid first, then the static page registry)
        and merged de-duplicated, so a sub-optimal model rewrite can never drop evidence
        the literal question would have found — the grounding stays stable under real
        function-calling decisions (evaluation LITERAL/SEMANTIC keep their numbers).

        IMPORTANT: the merged list must NOT be truncated to the primary path's size. A
        model query whose KB top-6 fills the slots would push every fallback candidate
        out (observed in WSL: LITERAL 8/8 -> 6/8 despite dual-path recall). Each path is
        naturally bounded (KB <= 6, static <= 3; KB non-empty skips static), so the
        merged list is at most ~12 — kept whole so the fallback evidence always survives.
        """
        merged: list[Candidate] = []
        seen: set[tuple[str, int]] = set()
        for query in (primary, fallback):
            kb = await self._knowledge_candidates(query, page_key, project_key)
            static = retrieve(query, page_key, project_key) if not kb else []
            for candidate in [*kb, *static]:
                key = (candidate.doc, candidate.fragment)
                if key not in seen:
                    seen.add(key)
                    merged.append(candidate)
        return merged

    async def _knowledge_candidates(
        self, question: str, page_key: str, project_key: str | None
    ) -> list[Candidate]:
        """Chunk-level hybrid retrieval (vector + BM25 fused with RRF, TASK-KB-RAG-001).

        KB results are scoped to the current page domain (``_kb_domain_docs``), so a
        projects page never pulls another project's chunks. Empty list falls back to
        static pages."""

        if self._knowledge_repository is None or self._embedder is None or self._storage is None:
            return []
        doc_names = _kb_domain_docs(page_key, project_key)
        if doc_names is not None and not doc_names:
            return []  # domain has no KB docs (e.g. projects/jianli) -> static only
        try:
            vector = (await asyncio.to_thread(self._embedder.embed, [question]))[0]
            vector_hits = await asyncio.to_thread(
                self._knowledge_repository.search_chunks,
                vector,
                min_score=self._min_score,
                doc_names=doc_names,
            )
            corpus = await asyncio.to_thread(
                self._knowledge_repository.load_chunk_corpus, doc_names=doc_names
            )
        except EmbeddingError:
            return []
        # P1 relevance threshold (TASK-KB-THRESHOLD-001): no semantically similar chunk
        # -> no evidence. BM25 single-char overlap alone must NOT ground an answer
        # (CJK single chars always overlap), otherwise irrelevant questions would be
        # answered instead of refused.
        if not vector_hits:
            return []
        bm25_hits = bm25.BM25Index(corpus).search(question, top_k=10)
        vector_ids = [str(hit["chunk_id"]) for hit in vector_hits]
        bm25_ids = [chunk_id for chunk_id, _ in bm25_hits]
        fused = bm25.reciprocal_rank_fusion(
            [
                [(chunk_id, 0.0) for chunk_id in vector_ids],
                [(chunk_id, 0.0) for chunk_id in bm25_ids],
            ],
            top_k=6,
        )
        if not fused:
            return []
        details = await asyncio.to_thread(
            self._knowledge_repository.chunk_rows, [chunk_id for chunk_id, _ in fused]
        )
        candidates: list[Candidate] = []
        for chunk_id, _ in fused:
            row = details.get(chunk_id)
            if row is None:
                continue
            candidates.append(
                Candidate(
                    doc=str(row["doc_name"]),
                    fragment=int(row["seq"]),
                    text=str(row["content"]),
                    score=1.0,
                )
            )
        return candidates

    async def _persist_assistant(
        self, conversation_id: UUID, content: str, is_offtopic: bool
    ) -> None:
        if self._repository is None:
            return
        now = default_now()
        await asyncio.to_thread(
            self._repository.append_message,
            conversation_id,
            role="assistant",
            content=content,
            is_offtopic=is_offtopic,
            now=now,
        )
        await asyncio.to_thread(self._repository.touch, conversation_id, now)

    # -- multi-turn memory backfill (TASK-M6-HARDENING-001) -------------------------------

    async def _load_history(self, conversation_id: UUID) -> list[dict[str, str]]:
        """Most recent prior messages for context injection (bounded, see _MAX_HISTORY_MESSAGES).

        Called before the current question is appended, so the history never includes the
        in-flight question. Only role/content are surfaced to the model.
        """
        if self._repository is None:
            return []
        rows = await asyncio.to_thread(self._repository.list_messages, conversation_id)
        return [
            {"role": row["role"], "content": row["content"]}
            for row in rows[-_MAX_HISTORY_MESSAGES:]
        ]

    # -- structured observability helpers (TASK-M6-HARDENING-001) -------------------------

    def _log_error(
        self, trace_id: str, conversation_id: UUID | None, error: Exception
    ) -> None:
        logger.error(
            "answer_error",
            extra={
                "trace_id": trace_id,
                "conversation_id": str(conversation_id) if conversation_id is not None else None,
                "error_type": type(error).__name__,
            },
        )

    def _log_offtopic(
        self, trace_id: str, conversation_id: UUID | None, start: float
    ) -> None:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "answer_offtopic",
            extra={
                "trace_id": trace_id,
                "conversation_id": str(conversation_id) if conversation_id is not None else None,
                "grounded": False,
                "offtopic": True,
                "model": _OFFTOPIC_CODE,
                "latency_ms": latency_ms,
            },
        )
