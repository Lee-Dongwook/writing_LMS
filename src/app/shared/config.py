from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 개발 편의용 기본 시크릿. 운영에서 이 값이 그대로면 부팅을 거부한다.
_INSECURE_JWT_SECRET = "dev-insecure-secret-change-me-in-production-please"
# 운영에서 요구하는 최소 시크릿 길이.
_MIN_JWT_SECRET_LEN = 32


class Settings(BaseSettings):
    """애플리케이션 전역 설정.

    값은 환경변수에서 로드된다. `.env` 파일 로딩은 `shared.init.load_dotenv`가
    별도로 담당하므로 여기서는 파일을 직접 읽지 않는다.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    # 실행 환경: development / local / production
    env: str = Field(default="development", alias="ENV")

    app_name: str = Field(default="Writing LMS", alias="APP_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # SQLAlchemy 비동기 DSN (예: postgresql+psycopg://user:pass@host:5432/db)
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/writing_lms",
        alias="DATABASE_URL",
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # LLM 프로바이더/모델. init_chat_model "provider:model" 규격.
    # 프로바이더 확정 후 env로 교체(예: "anthropic:claude-...", "openai:gpt-4o-mini").
    llm_model: str = Field(default="openai:gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    # Ollama(로컬 LLM). LLM_MODEL이 "ollama:..."일 때 base_url로 주입된다.
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")

    # OCR 백엔드 식별자(교체 가능). 기본 stub — 실제 백엔드는 리서치 후 선택.
    ocr_backend: str = Field(default="stub", alias="OCR_BACKEND")

    # 대화형 에이전트 체크포인터 백엔드: "memory"(기본, DB 불필요) | "postgres".
    # Postgres는 마이그레이션/체크포인터 테이블 준비 후 전환한다.
    agent_checkpointer: str = Field(default="memory", alias="AGENT_CHECKPOINTER")

    # 인증 (로컬 JWT). 운영 환경에서는 JWT_SECRET를 반드시 교체할 것.
    # 생성: `make gen-secret` (python -c "import secrets;print(secrets.token_urlsafe(48))")
    jwt_secret: str = Field(
        default=_INSECURE_JWT_SECRET,
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60 * 24,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # 어드민(교사) 부트스트랩 계정. `make seed-admin`이 이 값으로 계정을 upsert한다.
    # 비밀번호는 평문이 아니라 bcrypt 해시로 저장한다(운영 프레임).
    # 해시 생성: `make hash-password`. 미설정 시 시드는 건너뛴다.
    admin_email: str | None = Field(default=None, alias="ADMIN_EMAIL")
    admin_password_hash: str | None = Field(default=None, alias="ADMIN_PASSWORD_HASH")
    admin_name: str | None = Field(default=None, alias="ADMIN_NAME")

    # CORS 허용 오리진(콤마 구분). 예: "http://localhost:3000,https://app.example.com"
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def checkpoint_dsn(self) -> str:
        """LangGraph Postgres 체크포인터용 psycopg DSN.

        SQLAlchemy 드라이버 접미사(`+psycopg`, `+asyncpg`)를 제거한 순수 DSN을 반환한다.
        """
        return self.database_url.replace("+psycopg", "").replace("+asyncpg", "")

    @property
    def is_local(self) -> bool:
        return self.env == "local"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> Self:
        """운영 환경에서 안전하지 않은 JWT 시크릿을 거부한다(부팅 차단).

        개발/로컬에서는 기본 시크릿을 허용해 편의를 유지한다.
        """
        if self.is_production:
            if self.jwt_secret == _INSECURE_JWT_SECRET:
                msg = "운영 환경에서는 JWT_SECRET를 반드시 교체해야 합니다(`make gen-secret`)."
                raise ValueError(msg)
            if len(self.jwt_secret) < _MIN_JWT_SECRET_LEN:
                msg = f"JWT_SECRET는 최소 {_MIN_JWT_SECRET_LEN}자 이상이어야 합니다."
                raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """프로세스 전역에서 재사용되는 캐시된 설정 인스턴스."""
    return Settings()
