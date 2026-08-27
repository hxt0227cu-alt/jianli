#!/usr/bin/env python3
"""Validate the public Agent evaluation report without external dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "apps" / "web" / "evals" / "latest.json"
MAX_BYTES = 50 * 1024
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
CASE_CATEGORIES = {"expected_block", "known_limitation", "regression"}
CASE_STATUSES = {"verified", "open", "resolved"}
FORBIDDEN_KEYS = {
    "question",
    "answer",
    "answer_text",
    "prompt",
    "system_prompt",
    "knowledge_text",
    "email",
    "phone",
    "appointment_id",
    "secret",
    "api_key",
}


def _walk(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_KEYS.intersection(key.lower() for key in value)
        if forbidden:
            raise ValueError(f"public report contains forbidden keys: {sorted(forbidden)}")
        for nested in value.values():
            _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            _walk(nested)


def validate(report: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "report_id",
        "generated_at",
        "verified_commit",
        "environment",
        "overall",
        "ci",
        "suites",
        "comparisons",
        "cases",
    }
    if set(report) != required:
        raise ValueError(f"top-level schema mismatch: {sorted(set(report) ^ required)}")
    if report["schema_version"] != 2 or not COMMIT.fullmatch(report["verified_commit"]):
        raise ValueError("invalid schema_version or verified_commit")

    suites = report["suites"]
    if not isinstance(suites, list) or not suites:
        raise ValueError("suites must be a non-empty list")
    passed = 0
    total = 0
    for suite in suites:
        if set(suite) != {"id", "label", "passed", "total", "verified_commit", "evidence"}:
            raise ValueError(f"suite schema mismatch: {suite.get('id', '<unknown>')}")
        if not COMMIT.fullmatch(suite["verified_commit"]):
            raise ValueError(f"invalid suite commit: {suite['id']}")
        if not (0 <= suite["passed"] <= suite["total"] and suite["total"] > 0):
            raise ValueError(f"invalid suite totals: {suite['id']}")
        passed += suite["passed"]
        total += suite["total"]
    if report["overall"] != {"passed": passed, "total": total}:
        raise ValueError("overall totals do not equal suite totals")

    comparisons = report["comparisons"]
    if not isinstance(comparisons, list) or not comparisons:
        raise ValueError("comparisons must be a non-empty list")
    comparison_keys = {
        "id",
        "label",
        "evidence_level",
        "provider_model",
        "sample_size",
        "baseline",
        "reranked",
        "verified_commit",
    }
    for comparison in comparisons:
        if set(comparison) != comparison_keys:
            raise ValueError(f"comparison schema mismatch: {comparison.get('id', '<unknown>')}")
        if comparison["evidence_level"] != "real_provider_component_benchmark":
            raise ValueError(f"invalid comparison evidence: {comparison['id']}")
        if comparison["sample_size"] < 1 or not COMMIT.fullmatch(
            comparison["verified_commit"]
        ):
            raise ValueError(f"invalid comparison evidence: {comparison['id']}")

    cases = report["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")
    for case in cases:
        if set(case) != {"id", "category", "title", "status", "test_id"}:
            raise ValueError(f"case schema mismatch: {case.get('id', '<unknown>')}")
        if case["category"] not in CASE_CATEGORIES or case["status"] not in CASE_STATUSES:
            raise ValueError(f"invalid case enum: {case['id']}")
    _walk(report)


def main() -> int:
    size = REPORT.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(f"report is {size} bytes; limit is {MAX_BYTES}")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    validate(report)
    print(
        f"eval report valid: {report['overall']['passed']}/{report['overall']['total']} "
        f"checks, {len(report['cases'])} boundary cases, {size} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
