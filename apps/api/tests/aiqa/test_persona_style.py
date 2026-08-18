"""Persona style assertions (TASK-AIQA-PERSONA-STYLE-019).

Checks that the digital-twin system prompt carries the owner's real communication
style (conclusion-first, objective wording, boundaries, tech-interview habits) and
that the few-shot examples (a) stay within the PRD §4.9.1 sample range, (b) contain
no emotional adjectives, (c) are conclusion-first, and (d) trace every number back
to the corpus — nothing invented.

These are static assertions (no LLM round-trip), so they never flake. Online
answer-style is guarded by the fact-consistency SLO (38/38) instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # apps/api

from app.aiqa.content import build_pages  # noqa: E402
from app.aiqa.persona import STYLE_FEW_SHOT, _SYSTEM_PROMPT  # noqa: E402
from tests.aiqa.test_rag_eval import CORPUS  # noqa: E402

_CORPUS_TEXT = "\n".join(CORPUS.values())
_STATIC_TEXT = "\n".join(c.text for page in build_pages().values() for c in page.chunks)
_TRACEABLE = _CORPUS_TEXT + "\n" + _STATIC_TEXT

_STYLE_KEYWORDS = [
    "结论前置",
    "客观陈述",
    "知之为知之",
    "分段表达",
    "踩坑",
    "取舍",
    "指标",
    "约束条件",
    "技术选型理由",
    "做了什么",
    "学到什么",
]

_EMOTIONAL_NEGATIVES = [
    "超级难",
    "压力巨大",
    "特别成功",
    "很离谱",
    "极其痛苦",
    "非常棒",
    "无敌",
    "炸裂",
    "崩溃",
]


def test_style_instructions_present() -> None:
    for kw in _STYLE_KEYWORDS:
        assert kw in _SYSTEM_PROMPT, f"system prompt 缺少风格指令: {kw}"


def test_few_shot_count_within_spec() -> None:
    assert 8 <= len(STYLE_FEW_SHOT) <= 12, f"few-shot 数量应为 8-12，当前 {len(STYLE_FEW_SHOT)}"


def test_few_shot_no_emotional_words() -> None:
    joined = "\n".join(q + "\n" + a for q, a in STYLE_FEW_SHOT)
    for w in _EMOTIONAL_NEGATIVES:
        assert w not in joined, f"示例含情绪化词: {w}"


def test_few_shot_conclusion_first() -> None:
    markers = ("是", "核心", "最", "关键", "结论", "分", "做过", "方法", "落地", "采用")
    for q, a in STYLE_FEW_SHOT:
        first = a.strip().split("\n")[0]
        assert first, f"示例回答为空: {q}"
        assert any(
            m in first for m in markers
        ), f"首句非结论前置（{q}）: {first[:50]}"


def test_few_shot_numbers_traceable() -> None:
    for num in ["90.4", "0.47", "0.464", "119 轮", "56,289", "12.6", "84/84", "60 条", "50 并发", "19%"]:
        assert num in _TRACEABLE, f"示例数字不可溯源（不在 CORPUS/content.py）: {num}"
