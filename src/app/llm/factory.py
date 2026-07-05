from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain.chat_models import init_chat_model

from src.app.shared.config import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


def parse_provider(model_id: str) -> str:
    """모델 식별자("provider:model")에서 프로바이더를 추출한다.

    ollama 모델 태그 자체가 콜론을 포함하므로("exaone3.5:7.8b") 첫 콜론만 분리한다.
    """
    return model_id.partition(":")[0]


def get_chat_model(model: str | None = None, **overrides: Any) -> BaseChatModel:
    """설정 기반 채팅 모델을 생성한다(프로바이더 공용 팩토리).

    `LLM_MODEL`("provider:model" 규격)과 `LLM_TEMPERATURE`를 사용하며,
    ollama 프로바이더면 `OLLAMA_HOST`를 base_url로 주입한다. `overrides`로 개별
    파라미터를 덮어쓸 수 있다.
    """
    settings = get_settings()
    model_id = model or settings.llm_model

    kwargs: dict[str, Any] = {"temperature": settings.llm_temperature, **overrides}
    if parse_provider(model_id) == "ollama":
        kwargs.setdefault("base_url", settings.ollama_host)

    return init_chat_model(model_id, **kwargs)
