from __future__ import annotations

from typing import TYPE_CHECKING, cast

from langchain_core.messages import HumanMessage, SystemMessage

from src.app.llm.factory import get_chat_model
from src.app.writing.domain import Domain, classify_domain
from src.app.writing.domain_prompts import compose_system_prompt
from src.app.writing.schema import AnalyzeResponse, PassageAnalysis

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

# 이 값 미만의 확신도로 분류되면 도메인 렌즈 대신 generalist 프롬프트로 폴백한다.
_CONFIDENCE_THRESHOLD = 0.5


async def analyze_passage(
    passage: str,
    model: BaseChatModel | None = None,
    domain: Domain | None = None,
) -> PassageAnalysis:
    """수능 비문학 지문을 분석해 구조화 결과를 반환한다.

    `domain`을 주면 해당 도메인 렌즈로 튜닝된 프롬프트를 쓰고, None이면 generalist
    프롬프트를 쓴다. `model`을 주입하면 해당 모델을 사용한다(테스트/대체 프로바이더용).
    """
    chat = model or get_chat_model()
    structured = chat.with_structured_output(PassageAnalysis)
    messages = [
        SystemMessage(content=compose_system_prompt(domain)),
        HumanMessage(content=passage),
    ]
    return cast("PassageAnalysis", await structured.ainvoke(messages))


async def run_analysis(
    passage: str,
    model: BaseChatModel | None = None,
) -> AnalyzeResponse:
    """분류 → 도메인 렌즈 선택 → 분석의 전체 파이프라인.

    1) `classify_domain`으로 지문 도메인을 분류하고,
    2) 확신도가 임계값 이상이면 해당 도메인 렌즈로, 미만이면 generalist로 분석한다.

    선택한 렌즈(도메인)와 분석 결과를 함께 반환한다.
    """
    classification = await classify_domain(passage, model=model)
    domain = (
        classification.domain
        if classification.confidence >= _CONFIDENCE_THRESHOLD
        else None
    )
    analysis = await analyze_passage(passage, model=model, domain=domain)
    return AnalyzeResponse(classification=classification, analysis=analysis)


_REVISE_INSTRUCTION = (
    "\n\n[수정 작업]\n"
    "아래 [현재 분석]은 위 지문에 대한 기존 분석 결과입니다. 사용자의 [수정 요청]을 "
    "반영해 분석을 갱신하세요. 요청과 무관한 부분은 기존 내용을 그대로 유지하고, "
    "요청된 부분만 지문 논리에 근거해 정확히 고칩니다. 전체 분석을 다시 출력하세요."
)


async def revise_analysis(
    passage: str,
    current: PassageAnalysis,
    instruction: str,
    domain: Domain | None = None,
    model: BaseChatModel | None = None,
) -> PassageAnalysis:
    """기존 분석을 사용자 수정 요청에 따라 갱신한다(리뷰 게이트에서 사용).

    `domain`을 주면 최초 분석과 동일한 도메인 렌즈를 유지한다.
    """
    chat = model or get_chat_model()
    structured = chat.with_structured_output(PassageAnalysis)
    system = compose_system_prompt(domain) + _REVISE_INSTRUCTION
    user = (
        f"[지문]\n{passage}\n\n"
        f"[현재 분석]\n{current.model_dump_json(indent=2)}\n\n"
        f"[수정 요청]\n{instruction}"
    )
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    return cast("PassageAnalysis", await structured.ainvoke(messages))
