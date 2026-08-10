"""Environment-backed application settings without external settings packages."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
        }
        values: dict[str, str] = {}
        for field_name, env_name in fields.items():
            value = source.get(env_name)
            if value is not None:
                values[field_name] = value.upper() if field_name == "log_level" else value
        return cls.model_validate(values)
