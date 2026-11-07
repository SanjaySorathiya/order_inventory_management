"""Configuration precedence and invalid environment input checks."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch):
    for variable in ("OIM_APP_NAME", "OIM_ENVIRONMENT", "OIM_DEBUG"):
        monkeypatch.delenv(variable, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_work_without_dotenv(tmp_path):
    settings = Settings(_env_file=tmp_path / "missing.env")

    assert settings.app_name == "Order & Inventory Management API"
    assert settings.environment == "development"
    assert settings.debug is False


def test_process_environment_overrides_dotenv(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "OIM_APP_NAME=Local catalog\nOIM_ENVIRONMENT=test\nOIM_DEBUG=true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OIM_ENVIRONMENT", "production")
    monkeypatch.setenv("OIM_DEBUG", "false")

    settings = Settings(_env_file=dotenv)

    assert settings.app_name == "Local catalog"
    assert settings.environment == "production"
    assert settings.debug is False


@pytest.mark.parametrize(
    ("variable", "value", "field"),
    [
        ("OIM_ENVIRONMENT", "staging", "environment"),
        ("OIM_DEBUG", "not-a-boolean", "debug"),
        ("OIM_APP_NAME", "   ", "app_name"),
    ],
)
def test_invalid_environment_values_fail(variable, value, field, monkeypatch):
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert error.value.errors()[0]["loc"] == (field,)
