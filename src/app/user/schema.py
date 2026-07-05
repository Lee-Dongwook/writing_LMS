from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    """인증된 사용자 표현(응답/의존성 반환용)."""

    model_config = ConfigDict(from_attributes=True)

    uuid: str
    email: EmailStr
    name: str | None = None
    is_active: bool = True


class UserCreate(BaseModel):
    """사용자 생성 입력."""

    email: EmailStr
    password: str
    name: str | None = None
