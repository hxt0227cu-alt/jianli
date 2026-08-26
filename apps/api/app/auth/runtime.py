"""Runtime wiring for PostgreSQL and Redis auth dependencies."""

from __future__ import annotations

from dataclasses import dataclass

import redis
from sqlalchemy import Engine, create_engine

from app.config import Settings
from app.notifications.email import EmailSender

from .passwords import PasswordHasher
from .rate_limit import LoginRateLimiter, RedisClient
from .repository import AuthRepository
from .service import AuthService
from .tokens import SessionTokens


@dataclass(slots=True)
class AuthRuntime:
    service: AuthService
    tokens: SessionTokens
    allowed_origins: frozenset[str]
    engine: Engine
    redis_client: RedisClient

    def close(self) -> None:
        self.redis_client.close()
        self.engine.dispose()


def _console_code_sink(kind: str, recipient: str, code: str) -> None:
    """Emit a code only for an explicitly selected local/test terminal session."""

    print(
        f"[local-email-code] kind={kind} recipient={recipient} code={code}",
        flush=True,
    )


def build_auth_runtime(settings: Settings) -> AuthRuntime:
    if not settings.auth_configured:
        raise ValueError("complete auth settings are required")
    if (
        settings.environment.strip().lower() == "production"
        and not settings.notification_configured
    ):
        raise ValueError("production auth requires complete SMTP settings")
    assert settings.database_url and settings.redis_url
    assert settings.csrf_hmac_key and settings.rate_limit_hmac_key
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    client = redis.Redis.from_url(settings.redis_url, decode_responses=False)
    tokens = SessionTokens(settings.csrf_hmac_key.get_secret_value())
    email_sender = (
        EmailSender(settings)
        if settings.email_mode == "smtp" and settings.notification_configured
        else None
    )
    code_sink = _console_code_sink if settings.email_mode == "console" else None
    service = AuthService(
        AuthRepository(engine),
        PasswordHasher(),
        tokens,
        LoginRateLimiter(client, settings.rate_limit_hmac_key.get_secret_value()),
        email_sender,
        code_sink,
    )
    return AuthRuntime(service, tokens, frozenset(settings.allowed_origins), engine, client)
