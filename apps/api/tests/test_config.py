import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_read_supported_environment_values_only() -> None:
    settings = Settings.from_env(
        {
            "JIANLI_APP_TITLE": "Local API",
            "JIANLI_APP_VERSION": "1.2.3",
            "JIANLI_ENVIRONMENT": "test",
            "JIANLI_LOG_LEVEL": "debug",
            "JIANLI_API_HOST": "0.0.0.0",
            "JIANLI_API_PORT": "9100",
            "JIANLI_PASSWORD": "must-not-be-read",
        }
    )

    assert settings.app_title == "Local API"
    assert settings.app_version == "1.2.3"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 9100
    assert "must-not-be-read" not in repr(settings)


@pytest.mark.parametrize("environment", ["local", "test"])
def test_console_email_mode_is_limited_to_non_deployed_environments(environment: str) -> None:
    settings = Settings(environment=environment, email_mode="console")
    assert settings.email_mode == "console"


@pytest.mark.parametrize("environment", ["production", "staging", "preview"])
def test_console_email_mode_is_rejected_outside_local_and_test(environment: str) -> None:
    with pytest.raises(ValidationError, match="console email mode is allowed only"):
        Settings(environment=environment, email_mode="console")
