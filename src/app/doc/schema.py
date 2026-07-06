from __future__ import annotations

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict

# --- 파이프라인 정의 스키마 (Document.pipeline JSONB의 구조) -----------------------
#
# MVP는 `llm_call` 액션만 지원한다. tool_call / agent_call은 후속 확장 지점이며,
# 지금은 정의하지 않는다(서브에이전트 레지스트리·도구 실행기는 별도 작업).


class LLMCallAction(BaseModel):
    """LLM 호출 액션. 프롬프트 템플릿을 상태값으로 렌더링해 모델을 호출한다."""

    action_type: Literal["llm_call"] = "llm_call"
    output_key: str = Field(
        description="이 스텝의 출력을 상태(values)에 저장할 키. 이후 스텝 프롬프트에서 참조 가능.",
    )
    prompt: str = Field(
        description="사용자 프롬프트 템플릿. `{key}` 자리표시자는 상태값으로 치환된다.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="시스템 프롬프트 템플릿(선택). 동일하게 `{key}` 치환을 지원.",
    )
    model: str | None = Field(
        default=None,
        description='모델 오버라이드("provider:model"). 없으면 기본 LLM_MODEL 사용.',
    )


class SimpleStep(BaseModel):
    """파이프라인의 단일 스텝. 그래프의 한 노드로 컴파일된다."""

    name: str = Field(description="스텝(노드) 이름. 그래프 내에서 고유해야 한다.")
    action: LLMCallAction = Field(description="스텝이 수행할 액션(MVP: llm_call).")


class PipeLine(BaseModel):
    """문서의 실행 파이프라인. 스텝을 선형 StateGraph로 컴파일한다."""

    # 저장된 파이프라인 JSON에 미래 필드(input_mapping 등)가 있어도 깨지지 않게 무시한다.
    model_config = ConfigDict(extra="ignore")

    steps: list[SimpleStep] = Field(default_factory=list)


# --- LangGraph 실행 상태 ---------------------------------------------------------


def _merge_values(
    left: dict[str, Any] | None, right: dict[str, Any] | None
) -> dict[str, Any]:
    """스텝별 output_key 출력을 누적 병합하는 리듀서(우측 우선)."""
    return {**(left or {}), **(right or {})}


class AgentState(TypedDict):
    """파이프라인 실행 상태.

    - `values`: 폼 입력 + 스텝별 output_key 출력이 누적되는 딕셔너리.
    - `messages`: 실행 중 생성된 메시지(스트리밍·이력용).
    - `user_uuid`: 소유자 식별자(노드에서 참조 가능).
    """

    values: Annotated[dict[str, Any], _merge_values]
    messages: Annotated[list[Any], add_messages]
    user_uuid: str
