"""Security regression tests for environment-separated auth code delivery."""

from __future__ import annotations

import logging
from typing import Any

import pytest

from app.auth.runtime import build_auth_runtime
from app.auth.service import AuthService
from app.config import Settings


class _RecordingSender:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def send(self, recipient: str, subject: str, body: str) -> None:
        self.calls.append((recipient, subject, body))


class _FailingSender:
    def send(self, recipient: str, subject: str, body: str) -> None:
        raise RuntimeError(f"sensitive recipient={recipient} body={body}")


def _service(
    *, sender: Any = None, sink: Any = None
) -> AuthService:
    # These collaborators are unused by the private delivery boundary under test.
    unused = object()
    return AuthService(unused, unused, unused, unused, sender, sink)  # type: ignore[arg-type]


def _auth_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "local",
        "database_url": "postgresql+psycopg://user:pass@127.0.0.1:5432/test",
        "redis_url": "redis://127.0.0.1:6379/0",
        "csrf_hmac_key": "c" * 32,
        "rate_limit_hmac_key": "r" * 32,
        "allowed_origins": ("https://example.test",),
    }
    values.update(overrides)
    return Settings.model_validate(values)


def test_smtp_success_uses_sender_and_never_calls_console_sink() -> None:
    sender = _RecordingSender()
    leaked: list[tuple[str, str, str]] = []
    service = _service(sender=sender, sink=lambda *args: leaked.append(args))

    service._send_verification_email("person@example.test", "123456")

    assert len(sender.calls) == 1
    assert sender.calls[0][0] == "person@example.test"
    assert "123456" in sender.calls[0][2]
    assert leaked == []


def test_smtp_failure_is_best_effort_and_logs_no_sensitive_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = _service(sender=_FailingSender())

    with caplog.at_level(logging.WARNING, logger="jianli.auth.email"):
        service._send_reset_email("private@example.test", "654321")

    output = caplog.text
    assert "auth_email_delivery_failed" in output
    assert "kind=reset" in output
    assert "error_type=RuntimeError" in output
    assert "private@example.test" not in output
    assert "654321" not in output
    assert "sensitive recipient" not in output


def test_local_console_runtime_emits_code_only_to_explicit_terminal_sink(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime = build_auth_runtime(_auth_settings(email_mode="console"))
    try:
        runtime.service._send_verification_email("local@example.test", "111222")
    finally:
        runtime.close()

    output = capsys.readouterr().out
    assert "[local-email-code]" in output
    assert "kind=verification" in output
    assert "local@example.test" in output
    assert "111222" in output


def test_local_smtp_without_configuration_remains_silent_sink(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    runtime = build_auth_runtime(_auth_settings(email_mode="smtp"))
    try:
        with caplog.at_level(logging.INFO, logger="jianli.auth.email"):
            runtime.service._send_verification_email("silent@example.test", "333444")
    finally:
        runtime.close()

    assert capsys.readouterr().out == ""
    assert "silent@example.test" not in caplog.text
    assert "333444" not in caplog.text


def test_production_auth_requires_complete_smtp_configuration() -> None:
    settings = _auth_settings(environment="production", email_mode="smtp")

    with pytest.raises(ValueError, match="production auth requires complete SMTP settings"):
        build_auth_runtime(settings)
