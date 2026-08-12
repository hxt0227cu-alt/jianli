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


def build_auth_runtime(settings: Settings) -> AuthRuntime:
    if not settings.auth_configured:
        raise ValueError("complete auth settings are required")
    assert settings.database_url and settings.redis_url
    assert settings.csrf_hmac_key and settings.rate_limit_hmac_key
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    client = redis.Redis.from_url(settings.redis_url, decode_responses=False)
    tokens = SessionTokens(settings.csrf_hmac_key.get_secret_value())
    # Email delivery is best-effort: wired only when SMTP is configured at runtime.
    email_sender = EmailSender(settings) if settings.notification_configured else None
    service = AuthService(
        AuthRepository(engine),
        PasswordHasher(),
        tokens,
        LoginRateLimiter(client, settings.rate_limit_hmac_key.get_secret_value()),
        email_sender,
    )
    return AuthRuntime(service, tokens, frozenset(settings.allowed_origins), engine, client)
