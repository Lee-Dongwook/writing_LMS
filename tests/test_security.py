"""인증 크립토(비밀번호 해시 + JWT) 단위 테스트."""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from src.app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip():
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed)
    assert not verify_password("wrong-pw", hashed)


def test_verify_password_invalid_hash():
    # bcrypt 형식이 아닌 값도 예외 없이 False
    assert not verify_password("anything", "not-a-bcrypt-hash")


def test_jwt_roundtrip():
    token = create_access_token("user-42")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-42"


def test_jwt_tampered_rejected():
    token = create_access_token("user-42")
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token + "tamper")


def test_jwt_expired_rejected():
    token = create_access_token("user-42", expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
