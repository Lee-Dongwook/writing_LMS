from __future__ import annotations

from pydantic import BaseModel, Field


class OcrResult(BaseModel):
    """OCR 추출 결과."""

    text: str = Field(description="이미지에서 추출된 텍스트.")
    backend: str = Field(description="추출에 사용된 OCR 백엔드 식별자.")
