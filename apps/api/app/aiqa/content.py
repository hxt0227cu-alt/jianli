"""Static public page knowledge registry (M6 round 1).

This is the *only* place page content lives in round 1. It serves two contract
endpoints (``getPageContent``, ``listRecommendedQuestions``) and is the grounding
corpus for the RAG answer (``streamAnswer``). It deliberately requires **no database
table** so round 1 ships with zero migrations.

Handoff note for Codex: replace ``build_pages()`` with a DB-backed loader once
``knowledge_documents`` / ``knowledge_index_versions`` land (TASK-M6-DB, round 3).
Keep the ``PageContentData`` shape so retrieval, persona and the router need no change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# Single, explicit updated_at so the public API is stable and cacheable.
_UPDATED_AT = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class PageChunk:
    """One retrievable fragment. ``doc`` is a human label (never a storage_key)."""

    doc: str
    fragment: int
    text: str


@dataclass(slots=True)
class PageContentData:
    page_key: str
    title: str
    sections: list[dict[str, object]]
    updated_at: datetime
    chunks: list[PageChunk]
    recommendations: list[str]


def _chunk(doc: str, lines: list[str]) -> list[PageChunk]:
    return [PageChunk(doc=doc, fragment=i, text=text) for i, text in enumerate(lines)]


def build_pages() -> dict[str, PageContentData]:
    """Construct the in-memory page registry (placeholder content, ready to swap)."""

    resume_sections: list[dict[str, object]] = [
        {
            "heading": "简介",
            "body": (
                "我是一名后端与平台方向的工程师，关注高并发服务、数据建模与开发者体验。"
                "这个站点是我本人的数字分身，用来回答关于我经历的问题并承接面试预约。"
            ),
        },
        {
            "heading": "教育背景",
            "body": "计算机科学与技术本科，主修分布式系统、数据库与软件工程。",
        },
        {
            "heading": "工作经历",
            "body": (
                "曾负责预约与协作类系统的后端架构，落地过插槽快照、实时刷新与幂等写入；"
                "也做过内容问答与检索相关功能。偏好先设计后编码，重视可观测与可演进。"
            ),
        },
        {
            "heading": "技术栈",
            "body": (
                "Python / FastAPI、PostgreSQL、Redis、TypeScript、React；熟悉 RAG 与人格层问答。"
            ),
        },
    ]
    resume_chunks = _chunk(
        "简历",
        [
            "我是一名后端与平台方向的工程师，关注高并发服务、数据建模与开发者体验。",
            "我做过预约与协作系统的后端架构，落地过插槽快照、实时刷新与幂等写入。",
            "我偏好先设计后编码，重视可观测性、可演进性与契约测试。",
            "技术栈包括 Python/FastAPI、PostgreSQL、Redis、TypeScript 与 React。",
            "我也做过内容问答与检索相关功能，熟悉 RAG 与人格层问答的实现。",
        ],
    )

    projects_jianli: dict[str, object] = {
        "heading": "个人 AI 问答网站（jianli）",
        "body": (
            "面向个人的作品集站点：公开 RAG 问答（基于本人资料、越界拒答）、第一人称人格层、"
            "动态面试表实时刷新、对话式面试预约代理。技术栈 FastAPI + PostgreSQL + Redis + React。"
        ),
    }
    projects_sleep: dict[str, object] = {
        "heading": "睡眠分析（sleep202603_an）",
        "body": "一个睡眠数据可视化与分析原型，负责数据采集管道与前端看板。",
    }
    projects_sections: list[dict[str, object]] = [projects_jianli, projects_sleep]
    projects_chunks = [
        *_chunk(
            "jianli",
            [
                "jianli 是个人 AI 问答网站：公开 RAG 问答、人格层、面试表实时刷新与预约代理。",
                "jianli 技术栈为 FastAPI + PostgreSQL + Redis + React，后端强调契约与幂等。",
            ],
        ),
        *_chunk(
            "sleep202603_an",
            [
                "sleep202603_an 是睡眠数据可视化与分析原型，负责采集管道与前端看板。",
            ],
        ),
    ]

    return {
        "resume": PageContentData(
            page_key="resume",
            title="个人简历",
            sections=resume_sections,
            updated_at=_UPDATED_AT,
            chunks=resume_chunks,
            recommendations=[
                "你最擅长的技术方向是什么？",
                "你做过哪些高并发相关的系统？",
                "你为什么强调先设计后编码？",
            ],
        ),
        "projects": PageContentData(
            page_key="projects",
            title="项目作品",
            sections=projects_sections,
            updated_at=_UPDATED_AT,
            chunks=projects_chunks,
            recommendations=[
                "介绍一下 jianli 这个项目的技术选型。",
                "sleep202603_an 解决了什么问题？",
                "你在项目里最得意的一个设计决策是什么？",
            ],
        ),
    }


PAGES = build_pages()
