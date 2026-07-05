from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import select

from src.app.auth.security import hash_password, verify_password
from src.app.user.model import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_by_uuid(db: AsyncSession, user_uuid: str) -> User | None:
    result = await db.execute(select(User).where(User.uuid == user_uuid))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    """새 사용자를 생성한다. 이메일 중복 여부는 호출부에서 사전 검사한다."""
    user = User(
        uuid=str(uuid4()),
        email=email,
        name=name,
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """이메일/비밀번호로 사용자를 인증한다. 실패 시 None."""
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_or_create_user(
    db: AsyncSession,
    email: str,
    name: str | None = None,
) -> User:
    """이메일 기준 upsert. 외부 IdP(OIDC) 최초 로그인 시 사용할 헬퍼.

    비밀번호 없이 생성되므로 로컬 로그인은 불가하다(외부 인증 전용).
    """
    user = await get_user_by_email(db, email)
    if user is not None:
        return user
    user = User(
        uuid=str(uuid4()),
        email=email,
        name=name,
        hashed_password="",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
