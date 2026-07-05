from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth.security import decode_access_token
from src.app.auth.service import get_user_by_uuid
from src.app.shared.database import get_async_db
from src.app.user.schema import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def verify_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> UserRead:
    """Bearer 토큰을 검증하고 활성 사용자를 반환하는 FastAPI 의존성."""
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise _CREDENTIALS_EXC from exc

    user_uuid = payload.get("sub")
    if not user_uuid:
        raise _CREDENTIALS_EXC

    user = await get_user_by_uuid(db, user_uuid)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC

    return UserRead.model_validate(user)


CurrentUser = Annotated[UserRead, Depends(verify_token)]


async def verify_admin(user: CurrentUser) -> UserRead:
    """관리자 전용 의존성. 인증은 통과했으나 관리자가 아니면 403."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return user


CurrentAdmin = Annotated[UserRead, Depends(verify_admin)]
