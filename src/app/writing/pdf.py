from __future__ import annotations

from typing import TYPE_CHECKING

import anyio
import pymupdf

if TYPE_CHECKING:
    from src.app.ocr.base import OcrProvider


class PdfError(Exception):
    """PDF 처리 중 발생하는 오류."""


# 페이지 남용 방지 상한. 수능 지문 PDF는 보통 한 자릿수 페이지다.
_MAX_PAGES = 30
# 문서 전체 텍스트 레이어가 이 글자 수 미만이면 스캔본으로 보고 OCR 폴백한다.
_MIN_TEXT_LAYER_CHARS = 20
# 스캔 페이지 렌더 해상도(OCR 정확도와 속도의 절충).
_RENDER_DPI = 200


def _extract_text_layer(data: bytes) -> str:
    """PDF의 텍스트 레이어를 페이지 순서대로 추출해 합친다(동기)."""
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if doc.page_count > _MAX_PAGES:
            msg = f"페이지가 너무 많습니다({doc.page_count} > {_MAX_PAGES})."
            raise PdfError(msg)
        parts = [page.get_text().strip() for page in doc]
    return "\n\n".join(p for p in parts if p).strip()


def _render_pages_to_png(data: bytes) -> list[bytes]:
    """스캔 PDF의 각 페이지를 PNG 바이트로 렌더한다(동기)."""
    images: list[bytes] = []
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if doc.page_count > _MAX_PAGES:
            msg = f"페이지가 너무 많습니다({doc.page_count} > {_MAX_PAGES})."
            raise PdfError(msg)
        for page in doc:
            pix = page.get_pixmap(dpi=_RENDER_DPI)
            images.append(pix.tobytes("png"))
    return images


async def extract_pdf_text(data: bytes, provider: OcrProvider) -> tuple[str, str]:
    """PDF에서 지문 텍스트를 추출한다.

    텍스트 레이어가 충분하면 그대로 사용하고(OCR 불필요), 스캔본이라 텍스트가
    비어 있으면 페이지를 이미지로 렌더해 `provider`로 OCR한다.

    Returns:
        (추출 텍스트, 사용한 백엔드 라벨).

    Raises:
        PdfError: PDF 파싱 실패/페이지 초과.
        OcrError: 스캔 폴백에서 OCR 백엔드 미설정/추출 실패.
    """
    try:
        text = await anyio.to_thread.run_sync(_extract_text_layer, data)
    except PdfError:
        raise
    except Exception as exc:  # pymupdf가 던지는 다양한 파싱 오류를 일원화
        msg = f"PDF를 열 수 없습니다: {exc}"
        raise PdfError(msg) from exc

    if len(text) >= _MIN_TEXT_LAYER_CHARS:
        return text, "pymupdf-text"

    # 텍스트 레이어가 부실 → 스캔본으로 간주하고 OCR 폴백
    images = await anyio.to_thread.run_sync(_render_pages_to_png, data)
    ocr_parts = [
        (await provider.extract_text(img, "image/png")).strip() for img in images
    ]
    joined = "\n\n".join(p for p in ocr_parts if p).strip()
    return joined, f"pymupdf-ocr:{provider.name}"
