from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth.dependencies import CurrentUser
from src.app.auth.schema import RegisterRequest, Token
from src.app.auth.security import create_access_token
from src.app.auth.service import (
    authenticate_user,
    create_user,
    get_user_by_email,
)
from src.app.shared.database import get_async_db
from src.app.user.schema import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[AsyncSession, Depends(get_async_db)]


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
)
async def register(payload: RegisterRequest, db: DbSession) -> UserRead:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await create_user(
        db,
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token, summary="로그인 (토큰 발급)")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    # OAuth2 규격상 username 필드에 이메일을 담아 보낸다.
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.uuid, extra_claims={"email": user.email})
    return Token(access_token=token)


@router.get("/me", response_model=UserRead, summary="현재 사용자 정보")
async def me(current_user: CurrentUser) -> UserRead:
    return current_user
