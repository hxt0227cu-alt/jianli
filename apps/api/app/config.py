"""Environment-backed application settings without external settings packages."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
EmailMode = Literal["smtp", "console"]


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
    # Email delivery mode: "smtp" (default) uses the configured SMTP channel;
    # "console" is an explicit local/test-only terminal sink for verification codes.
    email_mode: EmailMode = "smtp"
    # Feishu channel (R13/R14, TASK-FEISHU-001): tenant_access_token credentials +
    # the Bitable table that mirrors appointments. Runtime-only secrets, never in source.
    feishu_app_id: str | None = None
    feishu_app_secret: SecretStr | None = None
    feishu_bitable_base_token: str | None = None
    feishu_bitable_table_id: str | None = None
    feishu_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    # Optional LLM gateway (Answer domain, M6). When unset the Answer service uses a
    # deterministic in-process StubGateway so the site runs and is testable with no LLM.
    llm_base_url: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    # LLM gateway retry budget (P0-1, TASK-M6-HARDENING-001): transient 5xx/network
    # failures are retried with exponential backoff up to this many attempts (>=1).
    llm_max_retries: int = Field(default=3, ge=1, le=5)
    # Optional embedding gateway, independent of the chat LLM (TASK-DEPLOY-001). Providers
    # like DeepSeek expose chat but no /embeddings, so keeping these separate lets the
    # knowledge base keep working (deterministic local hash embedding) while chat uses the
    # LLM. When unset, the local embedding gateway is used.
    llm_embedding_base_url: str | None = None
    llm_embedding_api_key: SecretStr | None = None
    llm_embedding_model: str | None = None
    # Knowledge base (M6 round 3): local-disk object storage for parsed text and the
    # embedding dimension (must match the vector(1024) column of migration 0007;
    # BGE-M3 via SiliconFlow is the approved real-embedding default).
    knowledge_storage_dir: str = Field(default="./var/knowledge", min_length=1)
    llm_embedding_dim: int = Field(default=1024, ge=64, le=4096)
    # Relevance threshold (P1, TASK-KB-THRESHOLD-001): minimum vector cosine similarity
    # for a chunk to be treated as evidence. None = unconfigured (disabled, legacy
    # hard-recall); 0 = explicitly disabled; >0 = active. Only meaningful with a real
    # semantic embedding — the local hash embedding has no semantic meaning, so a
    # positive threshold would wrongly reject hit cases there.
    kb_min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    # Optional Cross-Encoder after RRF. Unset credentials keep the original RRF order.
    rerank_base_url: str | None = None
    rerank_api_key: SecretStr | None = None
    rerank_model: str | None = None
    rerank_timeout_seconds: float = Field(default=3.0, gt=0, le=5)
    rerank_top_n: int = Field(default=6, ge=1, le=12)
    # Anonymous public grounded-answer cache; disabled unless explicitly enabled.
    semantic_cache_enabled: bool = False
    semantic_cache_similarity: float = Field(default=0.94, ge=0.0, le=1.0)
    semantic_cache_ttl_seconds: int = Field(default=600, ge=60, le=86400)
    semantic_cache_max_entries: int = Field(default=100, ge=1, le=500)
    # Independent provider circuit breakers share policy, never state.
    circuit_breaker_failure_threshold: int = Field(default=3, ge=1, le=20)
    circuit_breaker_recovery_seconds: float = Field(default=30.0, ge=1, le=300)
    observability_enabled: bool = False
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = Field(default="jianli-api", min_length=1, max_length=80)

    @model_validator(mode="after")
    def validate_email_delivery_environment(self) -> Settings:
        """Keep the plaintext console code sink out of deployed environments."""

        environment = self.environment.strip().lower()
        if self.email_mode == "console" and environment not in {"local", "test"}:
            raise ValueError("console email mode is allowed only in local or test environments")
        return self

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

    @property
    def feishu_configured(self) -> bool:
        """Return whether the Feishu channel can run (runtime-only secrets)."""

        return all(
            (
                self.database_url,
                self.feishu_app_id,
                self.feishu_app_secret,
                self.feishu_bitable_base_token,
                self.feishu_bitable_table_id,
            )
        )

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
            "email_mode": "JIANLI_EMAIL_MODE",
            "feishu_app_id": "JIANLI_FEISHU_APP_ID",
            "feishu_app_secret": "JIANLI_FEISHU_APP_SECRET",
            "feishu_bitable_base_token": "JIANLI_FEISHU_BITABLE_BASE_TOKEN",
            "feishu_bitable_table_id": "JIANLI_FEISHU_BITABLE_TABLE_ID",
            "feishu_timeout_seconds": "JIANLI_FEISHU_TIMEOUT_SECONDS",
            "llm_base_url": "JIANLI_LLM_BASE_URL",
            "llm_api_key": "JIANLI_LLM_API_KEY",
            "llm_model": "JIANLI_LLM_MODEL",
            "llm_timeout_seconds": "JIANLI_LLM_TIMEOUT_SECONDS",
            "llm_max_retries": "JIANLI_LLM_MAX_RETRIES",
            "llm_embedding_base_url": "JIANLI_LLM_EMBEDDING_BASE_URL",
            "llm_embedding_api_key": "JIANLI_LLM_EMBEDDING_API_KEY",
            "llm_embedding_model": "JIANLI_LLM_EMBEDDING_MODEL",
            "knowledge_storage_dir": "JIANLI_KNOWLEDGE_STORAGE_DIR",
            "llm_embedding_dim": "JIANLI_LLM_EMBEDDING_DIM",
            "kb_min_score": "JIANLI_KB_MIN_SCORE",
            "rerank_base_url": "JIANLI_RERANK_BASE_URL",
            "rerank_api_key": "JIANLI_RERANK_API_KEY",
            "rerank_model": "JIANLI_RERANK_MODEL",
            "rerank_timeout_seconds": "JIANLI_RERANK_TIMEOUT_SECONDS",
            "rerank_top_n": "JIANLI_RERANK_TOP_N",
            "semantic_cache_enabled": "JIANLI_SEMANTIC_CACHE_ENABLED",
            "semantic_cache_similarity": "JIANLI_SEMANTIC_CACHE_SIMILARITY",
            "semantic_cache_ttl_seconds": "JIANLI_SEMANTIC_CACHE_TTL_SECONDS",
            "semantic_cache_max_entries": "JIANLI_SEMANTIC_CACHE_MAX_ENTRIES",
            "circuit_breaker_failure_threshold": "JIANLI_CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "circuit_breaker_recovery_seconds": "JIANLI_CIRCUIT_BREAKER_RECOVERY_SECONDS",
            "observability_enabled": "JIANLI_OBSERVABILITY_ENABLED",
            "otel_exporter_otlp_endpoint": "JIANLI_OTEL_EXPORTER_OTLP_ENDPOINT",
            "otel_service_name": "JIANLI_OTEL_SERVICE_NAME",
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
