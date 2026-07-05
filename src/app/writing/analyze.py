from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from src.app.llm.factory import get_chat_model
from src.app.writing.prompt import analysis_system_prompt
from src.app.writing.schema import PassageAnalysis

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


async def analyze_passage(
    passage: str,
    model: BaseChatModel | None = None,
) -> PassageAnalysis:
    """수능 비문학 지문을 분석해 구조화 결과를 반환한다.

    `model`을 주입하면 해당 모델을 사용한다(테스트/대체 프로바이더용). 미지정 시
    설정 기반 모델을 생성한다.
    """
    chat = model or get_chat_model()
    structured = chat.with_structured_output(PassageAnalysis)
    messages = [
        SystemMessage(content=analysis_system_prompt),
        HumanMessage(content=passage),
    ]
    return await structured.ainvoke(messages)
