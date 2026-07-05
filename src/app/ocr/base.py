from __future__ import annotations

from typing import Protocol, runtime_checkable


class OcrError(Exception):
    """OCR 처리 중 발생하는 오류의 베이스."""


class OcrNotConfiguredError(OcrError):
    """OCR 백엔드가 선택/설정되지 않았을 때."""


@runtime_checkable
class OcrProvider(Protocol):
    """이미지에서 텍스트를 추출하는 OCR 백엔드 인터페이스.

    구현체는 `name`(백엔드 식별자)과 `extract_text`를 제공한다. 백엔드는
    설정(`OCR_BACKEND`)으로 교체된다 — Tesseract/EasyOCR/PaddleOCR/Vision LLM 등.
    """

    name: str

    async def extract_text(self, image: bytes, mime_type: str) -> str:
        """이미지 바이트에서 텍스트를 추출해 반환한다.

        추출 불가/미설정 시 `OcrError`(또는 하위 예외)를 던진다.
        """
        ...
