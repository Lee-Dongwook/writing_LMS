from __future__ import annotations

import logging
from typing import Any

from ollama import AsyncClient

from src.app.shared.config import get_settings

logger = logging.getLogger(__name__)


def ollama_model_tag(model_id: str) -> str | None:
    """`LLM_MODEL`이 ollama면 실제 모델 태그를 반환한다(예: "exaone3.5:7.8b")."""
    provider, _, rest = model_id.partition(":")
    return rest or None if provider == "ollama" else None


def _model_names(list_response: Any) -> list[str]:
    """ollama list 응답(pydantic/dict 혼용)에서 모델 이름 목록을 추출한다."""
    models = getattr(list_response, "models", None)
    if models is None and isinstance(list_response, dict):
        models = list_response.get("models", [])

    names: list[str] = []
    for m in models or []:
        name = getattr(m, "model", None)
        if name is None and isinstance(m, dict):
            name = m.get("model") or m.get("name")
        if name:
            names.append(name)
    return names


async def ollama_health() -> dict[str, Any]:
    """Ollama 서버 도달 여부와 대상 모델 준비 상태를 점검한다.

    서버가 없어도 예외를 던지지 않고 `reachable: False`로 보고한다.
    """
    settings = get_settings()
    host = settings.ollama_host
    target = ollama_model_tag(settings.llm_model)

    try:
        response = await AsyncClient(host=host).list()
    except Exception as exc:  # noqa: BLE001  # 서버 미가동 등 모든 연결 오류를 상태로 보고
        logger.debug("Ollama unreachable at %s: %s", host, exc)
        return {
            "reachable": False,
            "host": host,
            "error": str(exc),
            "models": [],
            "target_model": target,
            "target_available": False,
        }

    models = _model_names(response)
    return {
        "reachable": True,
        "host": host,
        "models": models,
        "target_model": target,
        "target_available": (target in models) if target else None,
    }
