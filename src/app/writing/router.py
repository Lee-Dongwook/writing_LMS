from __future__ import annotations

from fastapi import APIRouter, status

from src.app.writing.analyze import analyze_passage
from src.app.writing.schema import AnalyzeRequest, PassageAnalysis

router = APIRouter(prefix="/writing", tags=["writing"])


@router.post(
    "/analyze",
    response_model=PassageAnalysis,
    status_code=status.HTTP_200_OK,
    summary="비문학 지문 분석(중심문장/요약/어휘)",
)
async def analyze(payload: AnalyzeRequest) -> PassageAnalysis:
    # TODO(auth): 릴리스 전 CurrentUser 의존성으로 보호할 것.
    # v1은 DB/로그인 없이 데모 가능하도록 공개 상태로 둔다.
    return await analyze_passage(payload.passage)
