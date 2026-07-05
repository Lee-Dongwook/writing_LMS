from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.app.ocr.base import OcrError, OcrProvider
from src.app.ocr.factory import get_ocr_provider
from src.app.ocr.schema import OcrResult
from src.app.writing.analyze import run_analysis
from src.app.writing.pdf import PdfError, extract_pdf_text
from src.app.writing.schema import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/writing", tags=["writing"])

# 허용 이미지 MIME 타입
_ALLOWED_IMAGE_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/jpg", "image/webp"},
)
# 허용 PDF MIME 타입
_ALLOWED_PDF_TYPES = frozenset({"application/pdf"})

OcrDep = Annotated[OcrProvider, Depends(get_ocr_provider)]


def _validate_image(file: UploadFile) -> None:
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원되지 않는 이미지 형식입니다: {content_type or 'unknown'}. "
            f"허용: {', '.join(sorted(_ALLOWED_IMAGE_TYPES))}",
        )


def _validate_pdf(file: UploadFile) -> None:
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_PDF_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원되지 않는 형식입니다: {content_type or 'unknown'}. PDF만 허용됩니다.",
        )


async def _extract_text(file: UploadFile, provider: OcrProvider) -> str:
    _validate_image(file)
    data = await file.read()
    try:
        return await provider.extract_text(data, file.content_type or "")
    except OcrError as exc:
        # 백엔드 미설정/추출 실패 → 503 (서비스 미가용)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


async def _extract_pdf(file: UploadFile, provider: OcrProvider) -> tuple[str, str]:
    """PDF에서 (텍스트, 백엔드 라벨)을 추출한다. 스캔본이면 OCR로 폴백."""
    _validate_pdf(file)
    data = await file.read()
    try:
        return await extract_pdf_text(data, provider)
    except PdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except OcrError as exc:
        # 스캔 PDF인데 OCR 백엔드 미설정/실패 → 503
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="비문학 지문 분석(도메인 분류 → 렌즈 튜닝 → 중심문장/요약/어휘)",
)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    # TODO(auth): 릴리스 전 CurrentUser 의존성으로 보호할 것.
    # v1은 DB/로그인 없이 데모 가능하도록 공개 상태로 둔다.
    return await run_analysis(payload.passage)


@router.post(
    "/ocr",
    response_model=OcrResult,
    status_code=status.HTTP_200_OK,
    summary="이미지 지문 OCR (이미지 → 텍스트)",
)
async def ocr(
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 이미지 파일")],
) -> OcrResult:
    text = await _extract_text(file, provider)
    return OcrResult(text=text, backend=provider.name)


@router.post(
    "/analyze-image",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="이미지 지문 → OCR → 도메인 분류 → 분석",
)
async def analyze_image(
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 이미지 파일")],
) -> AnalyzeResponse:
    passage = await _extract_text(file, provider)
    if not passage.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="이미지에서 텍스트를 추출하지 못했습니다.",
        )
    return await run_analysis(passage)


@router.post(
    "/pdf",
    response_model=OcrResult,
    status_code=status.HTTP_200_OK,
    summary="PDF 지문 텍스트 추출(텍스트 레이어 우선, 스캔본은 OCR 폴백)",
)
async def pdf_extract(
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 PDF 파일")],
) -> OcrResult:
    text, backend = await _extract_pdf(file, provider)
    return OcrResult(text=text, backend=backend)


@router.post(
    "/analyze-pdf",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="PDF 지문 → 텍스트 추출 → 도메인 분류 → 분석",
)
async def analyze_pdf(
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 PDF 파일")],
) -> AnalyzeResponse:
    passage, _ = await _extract_pdf(file, provider)
    if not passage.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PDF에서 텍스트를 추출하지 못했습니다.",
        )
    return await run_analysis(passage)
