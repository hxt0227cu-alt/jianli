from __future__ import annotations

from scripts.seed_kb import _seed_state_errors

EXPECTED = {"resume.md", "litchi-overview.md"}


def _item(name: str, status: str = "indexed", reason: str | None = None) -> dict[str, str | None]:
    return {"name": name, "status": status, "failure_reason": reason}


def test_seed_state_accepts_exact_indexed_active_corpus() -> None:
    active = [_item("resume.md"), _item("litchi-overview.md")]

    assert _seed_state_errors(active, EXPECTED) == []


def test_seed_state_rejects_failed_documents_and_redacts_key() -> None:
    active = [
        _item("resume.md"),
        _item("litchi-overview.md", "failed", "provider 402 for sk-secret-value"),
    ]

    errors = _seed_state_errors(active, EXPECTED)

    assert errors == [
        "litchi-overview.md: status=failed, "
        "reason=provider 402 for sk-<redacted>"
    ]


def test_seed_state_rejects_missing_extra_and_duplicate_active_names() -> None:
    active = [
        _item("resume.md"),
        _item("resume.md"),
        _item("unexpected.md"),
    ]

    errors = _seed_state_errors(active, EXPECTED)

    assert errors == [
        "active count 3 != expected 2",
        "missing: litchi-overview.md",
        "unexpected: unexpected.md",
    ]
