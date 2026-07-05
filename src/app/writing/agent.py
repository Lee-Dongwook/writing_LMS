from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import InjectedState, ToolNode
from langgraph.types import Command, interrupt

from src.app.llm.factory import get_chat_model
from src.app.writing.analyze import revise_analysis, run_analysis
from src.app.writing.schema import AnalyzeResponse

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


class WritingAgentState(MessagesState):
    """writing 대화형 에이전트 상태.

    `messages`(대화 이력)에 더해, 분석 대상 지문·현재 분석 초안·리뷰 대기 여부를 담는다.
    분석 결과는 체크포인터 직렬화 안전을 위해 dict(model_dump)로 저장한다.
    """

    pending_passage: str | None
    analysis: dict[str, Any] | None
    awaiting_review: bool


def _summarize(result: AnalyzeResponse) -> str:
    """분석 초안을 LLM 대화 맥락용으로 짧게 요약한다(전체 JSON은 상태에 보관)."""
    a = result.analysis
    c = result.classification
    return (
        f"[분석 초안 생성됨] 도메인={c.domain.label}(확신도 {c.confidence:.2f}), "
        f"구조유형={a.summary.structure_type.value}. 중심문장 {len(a.key_sentences)}개 / "
        f"어휘 {len(a.vocabulary)}개 / 핵심화제='{a.summary.topic}'. "
        "리뷰 게이트에서 사용자 승인 또는 수정 지시를 기다립니다."
    )


@tool
async def analyze_passage_tool(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
    passage: str | None = None,
) -> Command:
    """수능 비문학 지문을 분석한다(중심문장/요약/어휘, 도메인 자동 분류).

    새 지문을 제시할 때는 passage에 지문 원문을 넣는다. 이미 업로드된 지문을 분석할
    때는 passage를 비워 두면 대화에 접수된 지문을 사용한다.
    """
    text = (passage or state.get("pending_passage") or "").strip()
    if not text:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "분석할 지문이 없습니다. 지문 텍스트를 입력하거나 파일을 업로드하세요.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            },
        )
    result = await run_analysis(text)
    return Command(
        update={
            "pending_passage": text,
            "analysis": result.model_dump(mode="json"),
            "awaiting_review": True,
            "messages": [ToolMessage(_summarize(result), tool_call_id=tool_call_id)],
        },
    )


@tool
async def revise_analysis_tool(
    instruction: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:
    """현재 분석 초안을 사용자의 수정 요청(instruction)대로 갱신한다.

    최초 분석과 동일한 도메인 렌즈를 유지하며, 요청된 부분만 고친다.
    """
    current = state.get("analysis")
    passage = state.get("pending_passage")
    if not current or not passage:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "수정할 분석 결과가 없습니다. 먼저 지문을 분석하세요.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            },
        )
    prev = AnalyzeResponse.model_validate(current)
    revised = await revise_analysis(
        passage,
        prev.analysis,
        instruction,
        domain=prev.classification.domain,
    )
    updated = AnalyzeResponse(classification=prev.classification, analysis=revised)
    return Command(
        update={
            "analysis": updated.model_dump(mode="json"),
            "awaiting_review": True,
            "messages": [ToolMessage(_summarize(updated), tool_call_id=tool_call_id)],
        },
    )


_TOOLS = [analyze_passage_tool, revise_analysis_tool]

_AGENT_SYSTEM = (
    "당신은 수능 국어 비문학 학습을 돕는 대화형 조교입니다. 사용자가 지문(텍스트/파일)을 "
    "제시하면 analyze_passage_tool로 분석하고, 분석 초안에 대한 수정 요청이 오면 "
    "revise_analysis_tool로 반영하세요. 분석/수정 결과는 리뷰 게이트에서 사용자 확인을 "
    "거칩니다. 사용자가 승인하면 간단히 확정 사실을 알리고, 그 외에는 대화로 안내하세요."
)


def _make_agent_node(
    model: BaseChatModel,
) -> Any:  # noqa: ANN401 - langgraph 노드 콜러블
    bound = model.bind_tools(_TOOLS)

    async def _agent(state: WritingAgentState) -> dict[str, Any]:
        from langchain_core.messages import SystemMessage

        messages = [SystemMessage(content=_AGENT_SYSTEM), *state["messages"]]
        response = await bound.ainvoke(messages)
        return {"messages": [response]}

    return _agent


async def _review_node(state: WritingAgentState) -> dict[str, Any]:
    """리뷰 게이트: 분석 초안을 제시하고 사용자의 승인/수정 지시를 기다린다(interrupt)."""
    decision = interrupt(
        {
            "type": "analysis_review",
            "message": "분석 초안입니다. 승인하려면 승인 의사를, 수정하려면 수정 내용을 알려주세요.",
            "analysis": state.get("analysis"),
        },
    )
    text = decision if isinstance(decision, str) else str(decision)
    return {"messages": [HumanMessage(content=text)], "awaiting_review": False}


def _route_after_agent(state: WritingAgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def _route_after_tools(state: WritingAgentState) -> str:
    return "review" if state.get("awaiting_review") else "agent"


def build_writing_agent(
    model: BaseChatModel | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """writing 대화형 ReAct 에이전트 그래프를 빌드한다(리뷰 게이트 interrupt 포함).

    `model`/`checkpointer`를 주입하면 테스트/대체 백엔드에 쓸 수 있다. 기본은 설정
    기반 모델 + 인메모리 체크포인터.
    """
    chat = model or get_chat_model()
    cp = checkpointer or _MEMORY_SAVER

    builder = StateGraph(WritingAgentState)
    builder.add_node("agent", _make_agent_node(chat))
    builder.add_node("tools", ToolNode(_TOOLS))
    builder.add_node("review", _review_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _route_after_agent, ["tools", END])
    builder.add_conditional_edges("tools", _route_after_tools, ["review", "agent"])
    builder.add_edge("review", "agent")
    return builder.compile(checkpointer=cp)


# 인메모리 체크포인터는 프로세스 내 스레드 상태를 유지하므로 싱글턴으로 둔다.
# (Postgres 전환 시 shared.database.get_checkpoint 로 교체)
_MEMORY_SAVER = MemorySaver()


@lru_cache
def get_writing_agent() -> CompiledStateGraph:
    """런타임용 컴파일된 에이전트(설정 모델 + 인메모리 체크포인터)."""
    return build_writing_agent()


def _config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


async def _finalize(graph: CompiledStateGraph, thread_id: str) -> dict[str, Any]:
    """실행/재개 후 스냅샷을 읽어 응답(인터럽트 or 완료)을 구성한다."""
    snapshot = await graph.aget_state(_config(thread_id))
    values = snapshot.values
    analysis = values.get("analysis")

    if snapshot.interrupts:
        return {
            "thread_id": thread_id,
            "status": "interrupted",
            "interrupt": snapshot.interrupts[0].value,
            "analysis": analysis,
        }

    reply = ""
    for message in reversed(values.get("messages", [])):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            reply = content if isinstance(content, str) else str(content)
            break
    return {
        "thread_id": thread_id,
        "status": "completed",
        "reply": reply,
        "analysis": analysis,
    }


async def send_message(
    thread_id: str,
    message: str,
    graph: CompiledStateGraph | None = None,
) -> dict[str, Any]:
    """대화 스레드에 텍스트 메시지를 보내고 다음 상태(인터럽트/완료)를 반환한다."""
    active = graph or get_writing_agent()
    await active.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        _config(thread_id),
    )
    return await _finalize(active, thread_id)


async def ingest_passage(
    thread_id: str,
    passage: str,
    note: str | None = None,
    graph: CompiledStateGraph | None = None,
) -> dict[str, Any]:
    """추출된 지문을 스레드에 주입하고 분석을 진행한다(파일 업로드 경로)."""
    active = graph or get_writing_agent()
    prompt = note or f"[첨부 지문 접수: {len(passage)}자] 이 지문을 분석해 주세요."
    await active.ainvoke(
        {"messages": [HumanMessage(content=prompt)], "pending_passage": passage},
        _config(thread_id),
    )
    return await _finalize(active, thread_id)


async def resume_review(
    thread_id: str,
    decision: str,
    graph: CompiledStateGraph | None = None,
) -> dict[str, Any]:
    """리뷰 게이트에서 사용자 결정(승인/수정 지시)으로 그래프를 재개한다."""
    active = graph or get_writing_agent()
    await active.ainvoke(Command(resume=decision), _config(thread_id))
    return await _finalize(active, thread_id)
