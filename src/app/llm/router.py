from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.app.llm.factory import parse_provider
from src.app.llm.ollama import ollama_health
from src.app.shared.config import get_settings

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/health", summary="LLM/Ollama 상태 점검")
async def health() -> dict[str, Any]:
    """현재 LLM 설정과, ollama 사용 시 서버/모델 준비 상태를 반환한다."""
    settings = get_settings()
    provider = parse_provider(settings.llm_model)

    info: dict[str, Any] = {
        "llm_model": settings.llm_model,
        "provider": provider,
    }
    if provider == "ollama":
        info["ollama"] = await ollama_health()
    return info
