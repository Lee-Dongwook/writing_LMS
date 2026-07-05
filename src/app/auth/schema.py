from __future__ import annotations

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """액세스 토큰 응답."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105  # OAuth2 표준 토큰 타입 문자열


class RegisterRequest(BaseModel):
    """회원가입 입력."""

    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    """로그인 입력(JSON 기반)."""

    email: EmailStr
    password: str
