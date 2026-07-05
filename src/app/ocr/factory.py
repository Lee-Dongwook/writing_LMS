from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from src.app.ocr.base import OcrNotConfiguredError
from src.app.ocr.stub import StubOcrProvider
from src.app.shared.config import get_settings

if TYPE_CHECKING:
    from src.app.ocr.base import OcrProvider

# 리서치 후 실제 백엔드를 여기에 등록한다. 각 백엔드는 옵셔널 의존성이므로
# 지연 import로 연결해, 미설치 백엔드가 앱 부팅을 막지 않게 한다.
_SUPPORTED_BACKENDS = ("stub",)  # 확장 예정: "tesseract", "easyocr", "paddleocr", "vision_llm"


@lru_cache
def get_ocr_provider() -> OcrProvider:
    """설정(`OCR_BACKEND`)에 맞는 OCR provider를 반환한다(FastAPI 의존성).

    미지원/미구현 백엔드는 `OcrNotConfiguredError`를 던진다.
    """
    backend = get_settings().ocr_backend.lower()

    if backend == "stub":
        return StubOcrProvider()

    # 예: 리서치 확정 후
    # if backend == "tesseract":
    #     from src.app.ocr.tesseract import TesseractOcrProvider
    #     return TesseractOcrProvider()

    raise OcrNotConfiguredError(
        f"지원되지 않는 OCR_BACKEND='{backend}'. 지원 값: {', '.join(_SUPPORTED_BACKENDS)}.",
    )
