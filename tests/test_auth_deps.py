"""관리자 의존성(verify_admin) 테스트."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.app.auth.dependencies import verify_admin
from src.app.user.schema import UserRead


async def test_verify_admin_allows_admin():
    admin = UserRead(uuid="a", email="admin@test.local", is_admin=True)
    assert await verify_admin(admin) is admin


async def test_verify_admin_blocks_non_admin():
    normal = UserRead(uuid="b", email="user@test.local", is_admin=False)
    with pytest.raises(HTTPException) as exc:
        await verify_admin(normal)
    assert exc.value.status_code == 403
