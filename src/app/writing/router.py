from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from src.app.auth.dependencies import CurrentUser
from src.app.ocr.base import OcrError, OcrProvider
from src.app.ocr.factory import get_ocr_provider
from src.app.ocr.schema import OcrResult
from src.app.writing.agent import (
    astream_ingest,
    astream_message,
    astream_resume,
    ingest_passage,
    resume_review,
    send_message,
)
from src.app.writing.analyze import run_analysis
from src.app.writing.pdf import PdfError, extract_pdf_text
from src.app.writing.schema import (
    AgentTurnResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ResumeRequest,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

router = APIRouter(prefix="/writing", tags=["writing"])

# SSE 응답 공통 헤더(프록시 버퍼링 방지 + 스트림 유지).
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

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
async def analyze(user: CurrentUser, payload: AnalyzeRequest) -> AnalyzeResponse:
    return await run_analysis(payload.passage)


@router.post(
    "/ocr",
    response_model=OcrResult,
    status_code=status.HTTP_200_OK,
    summary="이미지 지문 OCR (이미지 → 텍스트)",
)
async def ocr(
    user: CurrentUser,
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
    user: CurrentUser,
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
    user: CurrentUser,
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
    user: CurrentUser,
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


# --- 대화형 에이전트(human-in-the-loop) ---------------------------------------


def _thread_key(user: CurrentUser, client_thread: str) -> str:
    """클라이언트 스레드 식별자를 사용자 네임스페이스로 격리한다.

    체크포인터 thread_id를 `{user_uuid}:{client_thread}`로 구성하면, 다른 사용자가
    같은 client_thread 값을 제시해도 서로 다른 스레드로 매핑되어 접근이 차단된다.
    DB 소유권 테이블 없이 스레드를 사용자에 귀속시키는 경량 방식.
    """
    return f"{user.uuid}:{client_thread}"


def _turn_response(result: dict[str, Any], client_thread: str) -> AgentTurnResponse:
    """에이전트 실행 결과 dict를 API 응답 모델로 변환한다.

    `thread_uuid`는 내부 네임스페이스를 제거한 클라이언트 식별자로 되돌려준다
    (사용자 uuid 노출 방지 + 재개 시 동일 값 재사용).
    """
    return AgentTurnResponse(
        thread_uuid=client_thread,
        status=result["status"],
        reply=result.get("reply"),
        interrupt=result.get("interrupt"),
        analysis=result.get("analysis"),
    )


async def _extract_any(file: UploadFile, provider: OcrProvider) -> str:
    """이미지/PDF 파일에서 지문 텍스트를 추출한다(대화 업로드 경로)."""
    content_type = (file.content_type or "").lower()
    if content_type in _ALLOWED_PDF_TYPES:
        passage, _ = await _extract_pdf(file, provider)
        return passage
    return await _extract_text(file, provider)


@router.post(
    "/chat",
    response_model=AgentTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="대화형 분석: 메시지 전송(신규/기존 스레드)",
)
async def chat(user: CurrentUser, payload: ChatRequest) -> AgentTurnResponse:
    client_thread = payload.thread_uuid or uuid4().hex
    result = await send_message(_thread_key(user, client_thread), payload.message)
    return _turn_response(result, client_thread)


@router.post(
    "/chat/upload",
    response_model=AgentTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="대화 중 파일 업로드 → 지문 추출 → 분석(리뷰 게이트)",
)
async def chat_upload(
    user: CurrentUser,
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 이미지 또는 PDF")],
    thread_uuid: Annotated[str | None, Form(description="이어갈 스레드(없으면 신규)")] = None,
) -> AgentTurnResponse:
    passage = await _extract_any(file, provider)
    if not passage.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="파일에서 텍스트를 추출하지 못했습니다.",
        )
    client_thread = thread_uuid or uuid4().hex
    result = await ingest_passage(_thread_key(user, client_thread), passage)
    return _turn_response(result, client_thread)


@router.post(
    "/chat/resume",
    response_model=AgentTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="리뷰 게이트 재개(승인 또는 수정 지시)",
)
async def chat_resume(user: CurrentUser, payload: ResumeRequest) -> AgentTurnResponse:
    result = await resume_review(_thread_key(user, payload.thread_uuid), payload.decision)
    return _turn_response(result, payload.thread_uuid)


# --- SSE 스트리밍 엔드포인트 ---------------------------------------------------
# 이벤트 프레임: `event: <name>\n` + `data: <json>\n\n`. 클라이언트는 EventSource로
# run_started → message_chunk* → (interrupt) → run_finished / run_error를 수신한다.


def _sse_frame(event: dict[str, Any]) -> str:
    """표준 이벤트 dict를 SSE 텍스트 프레임으로 직렬화한다(UTF-8, ensure_ascii=False)."""
    name = event.get("event", "message")
    data = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {name}\ndata: {data}\n\n"


def _sse_response(events: AsyncGenerator[dict[str, Any]]) -> StreamingResponse:
    async def _frames() -> AsyncGenerator[str]:
        async for event in events:
            yield _sse_frame(event)

    return StreamingResponse(
        _frames(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post(
    "/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="대화형 분석(SSE): 메시지 전송 → 토큰/인터럽트 스트리밍",
)
async def chat_stream(user: CurrentUser, payload: ChatRequest) -> StreamingResponse:
    client_thread = payload.thread_uuid or uuid4().hex
    return _sse_response(astream_message(_thread_key(user, client_thread), payload.message))


@router.post(
    "/chat/upload/stream",
    status_code=status.HTTP_200_OK,
    summary="대화 중 파일 업로드 → 지문 추출 → 분석(SSE)",
)
async def chat_upload_stream(
    user: CurrentUser,
    provider: OcrDep,
    file: Annotated[UploadFile, File(description="지문 이미지 또는 PDF")],
    thread_uuid: Annotated[str | None, Form(description="이어갈 스레드(없으면 신규)")] = None,
) -> StreamingResponse:
    passage = await _extract_any(file, provider)
    if not passage.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="파일에서 텍스트를 추출하지 못했습니다.",
        )
    client_thread = thread_uuid or uuid4().hex
    return _sse_response(astream_ingest(_thread_key(user, client_thread), passage))


@router.post(
    "/chat/resume/stream",
    status_code=status.HTTP_200_OK,
    summary="리뷰 게이트 재개(SSE)",
)
async def chat_resume_stream(user: CurrentUser, payload: ResumeRequest) -> StreamingResponse:
    return _sse_response(
        astream_resume(_thread_key(user, payload.thread_uuid), payload.decision),
    )
