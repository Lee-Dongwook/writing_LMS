from __future__ import annotations

from src.app.ocr.base import OcrNotConfiguredError


class StubOcrProvider:
    """백엔드 미선택 상태의 기본 provider.

    앱이 OCR 시스템 의존성 없이도 부팅되도록 하되, 실제 호출 시에는 설정을 유도하는
    명확한 오류를 던진다. 리서치 후 실제 백엔드(예: tesseract/paddleocr)로 교체한다.
    """

    name = "stub"

    async def extract_text(self, image: bytes, mime_type: str) -> str:
        raise OcrNotConfiguredError(
            "OCR 백엔드가 설정되지 않았습니다. 환경변수 OCR_BACKEND를 지원되는 값으로 "
            "지정하세요(예: tesseract). 현재는 stub 상태입니다.",
        )
