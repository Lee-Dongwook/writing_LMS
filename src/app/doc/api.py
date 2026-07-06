from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter, ValidationError

from src.app.auth.dependencies import verify_token
from src.app.doc.forms import create_dynamic_model_from_elements
from src.app.doc.pipeline_service import run_pipeline
from src.app.doc.schema import PipeLine
from src.app.doc.service import get_doc_by_uuid
from src.app.shared.database import get_async_db, get_checkpoint

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.app.user.schema import UserRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doc", tags=["doc"])

# SSE 공통 헤더(프록시 버퍼링 방지 + 스트림 유지).
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def get_request_payload(request: Request) -> dict[str, Any]:
    """요청 본문을 dict로 파싱한다(JSON 우선, 폼 데이터 폴백)."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
        except (json.JSONDecodeError, ValueError):
            data = {}
        return data if isinstance(data, dict) else {}
    if "multipart/form-data" in content_type or "x-www-form-urlencoded" in content_type:
        return dict(await request.form())
    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _sse_frame(event: dict[str, Any]) -> str:
    """표준 이벤트 dict를 SSE 텍스트 프레임으로 직렬화한다."""
    name = event.get("event", "message")
    data = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {name}\ndata: {data}\n\n"


def _validate_payload(
    validation_model: type,
    payload: dict[str, Any],
    partial: bool,
) -> dict[str, Any]:
    """동적 모델로 payload를 검증한다. partial이면 제출된 필드만(재개용) 검증."""
    if not partial:
        return validation_model.model_validate(payload).model_dump()

    allowed = set(validation_model.model_fields.keys())
    validated: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    for key, value in payload.items():
        if key not in allowed:
            continue
        field = validation_model.model_fields[key]
        try:
            validated[key] = TypeAdapter(field.annotation).validate_python(value)
        except ValidationError as exc:
            errors.extend(
                {
                    "loc": [key, *err.get("loc", ())],
                    "msg": err["msg"],
                    "type": err["type"],
                }
                for err in exc.errors()
            )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors
        )
    return validated


@router.post(
    "/{doc_uuid}/dynamic_submit",
    summary="동적 폼 기반 문서 제출 → 파이프라인 실행(신규/재개, SSE 지원)",
    status_code=status.HTTP_200_OK,
)
async def submit_dynamic_form_endpoint(
    doc_uuid: str,
    request: Request,
    user: Annotated[UserRead, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    thread_uuid: Annotated[str | None, Query()] = None,
) -> Any:
    document = await get_doc_by_uuid(doc_uuid, user.uuid, db)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    payload = await get_request_payload(request)

    try:
        validation_model = create_dynamic_model_from_elements(
            f"DynamicFormModel_{doc_uuid}",
            document.inputs,
        )
        final_payload = _validate_payload(
            validation_model, payload, partial=bool(thread_uuid)
        )
    except HTTPException:
        raise
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동적 모델 생성/검증 실패: {exc}",
        ) from exc

    # 파이프라인 없는 신규 제출: 검증된 데이터만 반환.
    if not thread_uuid and not document.pipeline:
        return {"status": "success", "processed_data": final_payload}

    if not document.pipeline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="재개할 파이프라인이 문서에 정의되어 있지 않습니다.",
        )

    pipeline = PipeLine.model_validate(document.pipeline)
    streaming = "text/event-stream" in request.headers.get("accept", "")
    # 인터럽트/재개(다단계·기존 스레드)에는 체크포인터가 필요하다.
    needs_checkpoint = bool(thread_uuid) or len(pipeline.steps) > 1

    if streaming:
        return StreamingResponse(
            _stream_frames(
                document.uuid,
                pipeline,
                final_payload,
                user.uuid,
                thread_uuid,
                needs_checkpoint,
            ),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    final_res: dict[str, Any] = {}
    async for chunk in _run(
        document.uuid,
        pipeline,
        final_payload,
        user.uuid,
        thread_uuid,
        False,
        needs_checkpoint,
    ):
        final_res = chunk
    if final_res.get("status") == "pipeline_failed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=final_res)
    return final_res


async def _run(
    unique: str,
    pipeline: PipeLine,
    payload: dict[str, Any],
    user_uuid: str,
    thread_uuid: str | None,
    streaming: bool,
    needs_checkpoint: bool,
) -> AsyncGenerator[dict[str, Any]]:
    """체크포인터 컨텍스트(필요 시)에서 run_pipeline을 실행한다."""
    if needs_checkpoint:
        async with get_checkpoint() as cp:
            async for chunk in run_pipeline(
                unique=unique,
                pipeline=pipeline,
                user_uuid=user_uuid,
                payload=payload,
                thread_uuid=thread_uuid,
                streaming=streaming,
                checkpointer=cp,
            ):
                yield chunk
    else:
        async for chunk in run_pipeline(
            unique=unique,
            pipeline=pipeline,
            user_uuid=user_uuid,
            payload=payload,
            thread_uuid=thread_uuid,
            streaming=streaming,
            checkpointer=None,
        ):
            yield chunk


async def _stream_frames(
    unique: str,
    pipeline: PipeLine,
    payload: dict[str, Any],
    user_uuid: str,
    thread_uuid: str | None,
    needs_checkpoint: bool,
) -> AsyncGenerator[str]:
    """스트리밍 이벤트 dict를 SSE 프레임 문자열로 변환한다."""
    async for event in _run(
        unique, pipeline, payload, user_uuid, thread_uuid, True, needs_checkpoint
    ):
        yield _sse_frame(event)
