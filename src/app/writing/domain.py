from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, cast

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.app.llm.factory import get_chat_model

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class Domain(str, Enum):
    """수능 비문학 지문의 도메인 분류(6분류).

    실제 수능 출제 분야에 맞춘 상위 6분류. 값은 영문 슬러그(라우팅 키),
    표시는 한국어 라벨(`label`)을 쓴다. 융합 지문은 보조 도메인으로 표현한다.
    """

    HUMANITIES = "humanities"
    SOCIAL = "social"
    ECONOMICS = "economics"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ARTS = "arts"

    @property
    def label(self) -> str:
        return _DOMAIN_LABELS[self]


_DOMAIN_LABELS: dict[Domain, str] = {
    Domain.HUMANITIES: "인문",
    Domain.SOCIAL: "사회",
    Domain.ECONOMICS: "경제",
    Domain.SCIENCE: "과학",
    Domain.TECHNOLOGY: "기술",
    Domain.ARTS: "예술",
}

# 분류기가 참고할 도메인별 판단 기준(짧은 설명). 프롬프트에 주입된다.
_DOMAIN_GUIDE: dict[Domain, str] = {
    Domain.HUMANITIES: "철학·논리·윤리·역사·언어. 개념 정의와 관점 대립, 통시적 사상 전개.",
    Domain.SOCIAL: "법·정치·행정·사회학·문화. 제도와 요건-효과, 개념 위계.",
    Domain.ECONOMICS: "경제 이론·금융·시장. 변수 간 인과 모형과 조건부 변화.",
    Domain.SCIENCE: "물리·화학·생명·지구과학. 자연 현상의 원리와 메커니즘.",
    Domain.TECHNOLOGY: "공학·정보·기술 응용. 작동 원리에서 실제 적용으로의 과정.",
    Domain.ARTS: "미학·음악·미술·건축. 사조·기법과 미적 개념의 대비.",
}


class DomainClassification(BaseModel):
    """지문 도메인 분류 결과."""

    domain: Domain = Field(description="지문의 주 도메인(6분류 중 하나).")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="주 도메인 분류에 대한 확신도(0.0~1.0).",
    )
    secondary_domain: Domain | None = Field(
        default=None,
        description="융합 지문일 때 함께 걸치는 보조 도메인. 단일 도메인이면 null.",
    )
    rationale: str = Field(description="분류 근거를 한 문장으로.")


def _classification_system_prompt() -> str:
    lines = [
        "당신은 수능 국어 비문학(독서) 지문을 분야별로 분류하는 분류기입니다.",
        "아래 6개 도메인 중 지문의 주 도메인을 하나 고르고, 확신도(0~1)를 매기세요.",
        "두 분야에 걸친 융합 지문이면 secondary_domain에 보조 도메인을 지정하세요.",
        "",
        "[도메인 기준]",
    ]
    lines.extend(f"- {d.label}({d.value}): {_DOMAIN_GUIDE[d]}" for d in Domain)
    lines.extend(
        [
            "",
            "지문 전체를 읽을 필요는 없습니다. 도입부와 반복되는 핵심어로 판단하되,",
            "특정 분야로 단정하기 어려우면 confidence를 낮게 매기세요.",
        ],
    )
    return "\n".join(lines)


async def classify_domain(
    passage: str,
    model: BaseChatModel | None = None,
) -> DomainClassification:
    """지문을 6개 도메인 중 하나로 분류한다.

    분류는 분석보다 가벼운 작업이므로 temperature=0으로 결정적으로 수행한다.
    `model`을 주입하면 해당 모델을 사용한다(테스트/대체 프로바이더용).
    """
    chat = model or get_chat_model(temperature=0)
    structured = chat.with_structured_output(DomainClassification)
    messages = [
        SystemMessage(content=_classification_system_prompt()),
        HumanMessage(content=passage),
    ]
    return cast("DomainClassification", await structured.ainvoke(messages))
