"""Environment-backed application settings without external settings packages."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseModel):
    """Non-sensitive settings used by process entry points."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    app_title: str = Field(default="Jianli API", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)
    environment: str = Field(default="local", min_length=1)
    log_level: LogLevel = "INFO"
    api_host: str = Field(default="127.0.0.1", min_length=1)
    api_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str | None = None
    redis_url: str | None = None
    csrf_hmac_key: SecretStr | None = None
    rate_limit_hmac_key: SecretStr | None = None
    allowed_origins: tuple[str, ...] = ()
    field_encryption_current_key_id: str | None = None
    field_encryption_keys: SecretStr | None = None
    company_fingerprint_hmac_key: SecretStr | None = None
    appointment_confirmation_hmac_key: SecretStr | None = None
    smtp_host: str | None = None
    smtp_port: int = Field(default=465, ge=1, le=65535)
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    # Optional LLM gateway (Answer domain, M6). When unset the Answer service uses a
    # deterministic in-process StubGateway so the site runs and is testable with no LLM.
    llm_base_url: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    # Optional embedding gateway, independent of the chat LLM (TASK-DEPLOY-001). Providers
    # like DeepSeek expose chat but no /embeddings, so keeping these separate lets the
    # knowledge base keep working (deterministic local hash embedding) while chat uses the
    # LLM. When unset, the local embedding gateway is used.
    llm_embedding_base_url: str | None = None
    llm_embedding_api_key: SecretStr | None = None
    llm_embedding_model: str | None = None
    # Knowledge base (M6 round 3): local-disk object storage for parsed text and the
    # embedding dimension (must match the vector(768) column of migration 0005).
    knowledge_storage_dir: str = Field(default="./var/knowledge", min_length=1)
    llm_embedding_dim: int = Field(default=768, ge=64, le=4096)

    @property
    def auth_configured(self) -> bool:
        """Return whether every security-critical auth setting is present."""

        return all(
            (
                self.database_url,
                self.redis_url,
                self.csrf_hmac_key,
                self.rate_limit_hmac_key,
                self.allowed_origins,
            )
        )

    @property
    def booking_configured(self) -> bool:
        """Return whether every approved booking secret is present."""

        return all(
            (
                self.auth_configured,
                self.field_encryption_current_key_id,
                self.field_encryption_keys,
                self.company_fingerprint_hmac_key,
                self.appointment_confirmation_hmac_key,
            )
        )

    @property
    def notification_configured(self) -> bool:
        """Return whether the SMTP notification channel can run (runtime-only secrets)."""

        return all((self.database_url, self.smtp_host, self.smtp_user, self.smtp_password))

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Load only supported variables; unknown values, including secrets, are ignored."""

        source = os.environ if environ is None else environ
        fields = {
            "app_title": "JIANLI_APP_TITLE",
            "app_version": "JIANLI_APP_VERSION",
            "environment": "JIANLI_ENVIRONMENT",
            "log_level": "JIANLI_LOG_LEVEL",
            "api_host": "JIANLI_API_HOST",
            "api_port": "JIANLI_API_PORT",
            "database_url": "JIANLI_DATABASE_URL",
            "redis_url": "JIANLI_REDIS_URL",
            "csrf_hmac_key": "JIANLI_CSRF_HMAC_KEY",
            "rate_limit_hmac_key": "JIANLI_RATE_LIMIT_HMAC_KEY",
            "allowed_origins": "JIANLI_ALLOWED_ORIGINS",
            "field_encryption_current_key_id": "JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID",
            "field_encryption_keys": "JIANLI_FIELD_ENCRYPTION_KEYS",
            "company_fingerprint_hmac_key": "JIANLI_COMPANY_FINGERPRINT_HMAC_KEY",
            "appointment_confirmation_hmac_key": "JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY",
            "smtp_host": "JIANLI_SMTP_HOST",
            "smtp_port": "JIANLI_SMTP_PORT",
            "smtp_user": "JIANLI_SMTP_USER",
            "smtp_password": "JIANLI_SMTP_PASSWORD",
            "smtp_from": "JIANLI_SMTP_FROM",
            "llm_base_url": "JIANLI_LLM_BASE_URL",
            "llm_api_key": "JIANLI_LLM_API_KEY",
            "llm_model": "JIANLI_LLM_MODEL",
            "llm_timeout_seconds": "JIANLI_LLM_TIMEOUT_SECONDS",
            "llm_embedding_base_url": "JIANLI_LLM_EMBEDDING_BASE_URL",
            "llm_embedding_api_key": "JIANLI_LLM_EMBEDDING_API_KEY",
            "llm_embedding_model": "JIANLI_LLM_EMBEDDING_MODEL",
            "knowledge_storage_dir": "JIANLI_KNOWLEDGE_STORAGE_DIR",
            "llm_embedding_dim": "JIANLI_LLM_EMBEDDING_DIM",
        }
        values: dict[str, object] = {}
        for field_name, env_name in fields.items():
            value = source.get(env_name)
            if value is not None:
                if field_name == "log_level":
                    values[field_name] = value.upper()
                elif field_name == "allowed_origins":
                    values[field_name] = tuple(
                        item.strip() for item in value.split(",") if item.strip()
                    )
                else:
                    values[field_name] = value
        return cls.model_validate(values)
