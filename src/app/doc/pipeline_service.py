from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from src.app.doc.schema import AgentState, LLMCallAction, PipeLine, SimpleStep
from src.app.llm.factory import get_chat_model

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from langchain_core.runnables import RunnableConfig
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)

# 선형 그래프 빌더(structure 키 기준 캐시). 컴파일은 체크포인터/인터럽트가 요청마다
# 달라질 수 있으므로 매 호출 수행한다(빌더 재사용으로 노드 구성 비용만 절감).
_PIPELINE_BUILDER_CACHE: dict[str, StateGraph] = {}

# 프롬프트 템플릿의 `{key}` 자리표시자 패턴.
_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def render_template(template: str, values: dict[str, Any]) -> str:
    """`{key}` 자리표시자를 상태값으로 치환한다. 없는 키는 원문 그대로 둔다."""

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values[key]) if key in values else match.group(0)

    return _PLACEHOLDER.sub(_sub, template)


def _prepare_payload_for_agent(payload: Any) -> Any:
    """FileInfo dict를 file_url 문자열로 치환해 프롬프트에서 바로 쓸 수 있게 한다."""
    if isinstance(payload, dict):
        if isinstance(payload.get("file_url"), str):
            return payload["file_url"]
        return {k: _prepare_payload_for_agent(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [_prepare_payload_for_agent(item) for item in payload]
    return payload


# --- 액션 실행기 ----------------------------------------------------------------


async def execute_llm_call(
    action: LLMCallAction,
    state: AgentState,
    config: RunnableConfig,  # noqa: ARG001  # 시그니처 통일(향후 configurable 사용)
) -> AIMessage:
    """LLM 호출 액션을 실행한다. 프롬프트를 상태값으로 렌더링해 모델을 호출."""
    values = state["values"]
    messages: list[Any] = []
    if action.system_prompt:
        messages.append(
            SystemMessage(content=render_template(action.system_prompt, values))
        )
    messages.append(HumanMessage(content=render_template(action.prompt, values)))

    chat = get_chat_model(action.model)
    result = await chat.ainvoke(messages)
    return result if isinstance(result, AIMessage) else AIMessage(content=str(result))


# --- 그래프 빌드 ----------------------------------------------------------------


def _create_node_function(step: SimpleStep) -> Callable:
    async def _node(state: AgentState, config: RunnableConfig) -> dict:
        logger.info("--- 스텝 실행: %s ---", step.name)
        action = step.action
        if action.action_type == "llm_call":
            result = await execute_llm_call(action, state, config)
            return {"values": {action.output_key: result.content}, "messages": [result]}
        # MVP는 llm_call만 지원. tool_call / agent_call은 후속 확장.
        raise NotImplementedError(f"지원되지 않는 액션 타입: {action.action_type}")

    return _node


def _get_builder(unique: str, pipeline: PipeLine) -> StateGraph:
    """스텝 구성으로 선형 StateGraph 빌더를 만든다(구조 키 기준 캐시)."""
    structure_key = str(unique) + "-".join(s.name for s in pipeline.steps)
    cached = _PIPELINE_BUILDER_CACHE.get(structure_key)
    if cached is not None:
        return cached

    graph = StateGraph(AgentState)
    for step in pipeline.steps:
        graph.add_node(step.name, _create_node_function(step))

    if pipeline.steps:
        graph.set_entry_point(pipeline.steps[0].name)
        for prev, nxt in zip(pipeline.steps, pipeline.steps[1:], strict=False):
            graph.add_edge(prev.name, nxt.name)
        graph.add_edge(pipeline.steps[-1].name, END)

    _PIPELINE_BUILDER_CACHE[structure_key] = graph
    return graph


def _compile_pipeline(
    unique: str,
    pipeline: PipeLine,
    checkpointer: BaseCheckpointSaver | None,
) -> CompiledStateGraph:
    """빌더를 체크포인터/인터럽트 설정과 함께 컴파일한다.

    스텝이 2개 이상이면 각 스텝 이후 인터럽트(human-in-the-loop)를 건다.
    인터럽트/재개에는 체크포인터가 필요하다.
    """
    builder = _get_builder(unique, pipeline)
    interrupt_after = (
        [s.name for s in pipeline.steps[:-1]] if len(pipeline.steps) > 1 else []
    )
    return builder.compile(
        name="doc_pipeline",
        checkpointer=checkpointer,
        interrupt_after=interrupt_after,
    )


# --- 실행 ----------------------------------------------------------------------


async def run_pipeline(
    unique: str,
    pipeline: PipeLine,
    user_uuid: str,
    payload: dict | None = None,
    thread_uuid: str | None = None,
    streaming: bool = False,
    checkpointer: BaseCheckpointSaver | None = None,
) -> AsyncGenerator[dict[str, Any]]:
    """파이프라인 그래프를 초기화(신규)하거나 재개(thread_uuid)해 실행한다.

    - streaming=True: 표준 이벤트(run_started/step_started/message_chunk/interrupt/
      run_finished)를 순차적으로 방출한다.
    - streaming=False: 최종 상태 dict 하나(pipeline_completed/interrupted/failed)를 방출한다.
    """
    thread_id = thread_uuid or uuid4().hex
    values = _prepare_payload_for_agent(payload or {})

    graph = _compile_pipeline(unique, pipeline, checkpointer)
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id, "user_uuid": user_uuid},
        "recursion_limit": 25,
    }

    # 재개 판단: 기존 스레드가 인터럽트/미완 상태면 resume 커맨드로 이어간다.
    resume: Command | None = None
    if thread_uuid and checkpointer is not None:
        snapshot = await graph.aget_state(config)
        if snapshot and (snapshot.interrupts or snapshot.next):
            logger.info("thread %s 재개", thread_id)
            resume = Command(resume=True)

    initial_state = {"values": values, "user_uuid": user_uuid, "messages": []}
    graph_input: Any = resume if resume is not None else initial_state

    if streaming:
        async for event in astream_graph(graph, graph_input, thread_id, config):
            yield event
        return

    try:
        await graph.ainvoke(graph_input, config=config)
    except Exception as exc:  # noqa: BLE001  # 실행 실패를 프로토콜 dict로 변환해 반환
        logger.error("파이프라인 실행 실패", exc_info=True)
        yield {
            "status": "pipeline_failed",
            "message": f"파이프라인 실행 중 오류: {exc}",
            "thread_uuid": thread_id,
            "error_details": str(exc),
        }
        return

    snapshot = await graph.aget_state(config) if checkpointer is not None else None
    final_values = (snapshot.values.get("values", {}) if snapshot else {}) or {}

    if snapshot and snapshot.next:
        yield {
            "status": "pipeline_interrupted",
            "message": "파이프라인이 인터럽트되었습니다. 재개를 대기합니다.",
            "thread_uuid": thread_id,
            "current_state": final_values,
            "next_node_names": list(snapshot.next),
        }
    else:
        yield {
            "status": "pipeline_completed",
            "message": "파이프라인이 정상 완료되었습니다.",
            "thread_uuid": thread_id,
            "final_state": final_values,
        }


# --- 스트리밍 이벤트 ------------------------------------------------------------


def _ts() -> int:
    return int(time.time() * 1000)


async def astream_graph(
    graph: CompiledStateGraph,
    graph_input: Any,
    thread_uuid: str,
    config: RunnableConfig,
) -> AsyncGenerator[dict[str, Any]]:
    """그래프 실행을 표준 이벤트로 스트리밍한다(SSE 프레임으로 직렬화되는 dict)."""
    meta = {"thread_uuid": thread_uuid, "timestamp": _ts()}
    yield {"event": "run_started", "metadata": {**meta, "timestamp": _ts()}}

    last_ai: AIMessage | None = None
    try:
        async for mode, chunk in graph.astream(
            input=graph_input,
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "messages":
                message, _ = chunk
                if isinstance(message, AIMessageChunk) and message.content:
                    yield {
                        "event": "message_chunk",
                        "data": {"content": message.content, "message_id": message.id},
                        "metadata": {**meta, "timestamp": _ts()},
                    }
                continue

            # mode == "updates": 노드별 출력
            for node_name, node_output in chunk.items():
                if node_name == "__interrupt__":
                    interrupts = node_output or ()
                    value = interrupts[0].value if interrupts else None
                    yield {
                        "event": "interrupt",
                        "data": {"node_name": None, "value": value},
                        "metadata": {**meta, "timestamp": _ts()},
                    }
                    continue

                yield {
                    "event": "step_started",
                    "data": {"node_name": node_name},
                    "metadata": {**meta, "timestamp": _ts()},
                }
                if isinstance(node_output, dict):
                    for msg in reversed(node_output.get("messages", [])):
                        if isinstance(msg, AIMessage):
                            last_ai = msg
                            break

        data = {"content": last_ai.content, "message_id": last_ai.id} if last_ai else {}
        yield {
            "event": "run_finished",
            "data": data,
            "metadata": {**meta, "timestamp": _ts()},
        }

    except Exception as exc:  # noqa: BLE001  # 스트림 오류를 이벤트로 변환
        logger.error("astream_graph 오류", exc_info=True)
        yield {
            "event": "run_error",
            "data": {"message": str(exc)},
            "metadata": {**meta, "timestamp": _ts()},
        }
