"""운영 환경 설정 가드(JWT/DB 기본값 거부) 테스트."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.app.shared.config import (
    _INSECURE_DATABASE_URL,
    _INSECURE_JWT_SECRET,
    Settings,
)

_STRONG_SECRET = "x" * 40
_CUSTOM_DB = "postgresql+psycopg://u:p@db.internal:5432/prod"


def test_production_rejects_insecure_jwt(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", _INSECURE_JWT_SECRET)
    monkeypatch.setenv("DATABASE_URL", _CUSTOM_DB)
    with pytest.raises(ValidationError):
        Settings()


def test_production_rejects_short_jwt(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "too-short")
    monkeypatch.setenv("DATABASE_URL", _CUSTOM_DB)
    with pytest.raises(ValidationError):
        Settings()


def test_production_rejects_default_db_url(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", _STRONG_SECRET)
    monkeypatch.setenv("DATABASE_URL", _INSECURE_DATABASE_URL)
    with pytest.raises(ValidationError):
        Settings()


def test_production_accepts_strong_config(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", _STRONG_SECRET)
    monkeypatch.setenv("DATABASE_URL", _CUSTOM_DB)
    settings = Settings()
    assert settings.is_production


def test_development_allows_defaults(monkeypatch):
    # 개발 환경에서는 기본 시크릿/DSN도 허용(부팅 편의)
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("JWT_SECRET", _INSECURE_JWT_SECRET)
    monkeypatch.setenv("DATABASE_URL", _INSECURE_DATABASE_URL)
    settings = Settings()
    assert not settings.is_production
