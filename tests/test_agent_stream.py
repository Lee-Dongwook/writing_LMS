"""대화형 에이전트 SSE 스트리밍 이벤트 시퀀스."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import interrupt

from src.app.writing import agent as agent_mod


class _FakeToolModel(GenericFakeChatModel):
    """bind_tools를 무시하고 자기 자신을 반환하는 스트리밍용 가짜 모델."""

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN003, ANN201, ARG002
        return self


async def _collect(stream) -> list[dict[str, Any]]:
    return [event async for event in stream]


async def test_stream_emits_message_chunks_then_finished():
    model = _FakeToolModel(messages=iter([AIMessage(content="안녕하세요 지문을 올려주세요")]))
    graph = agent_mod.build_writing_agent(model=model, checkpointer=MemorySaver())

    events = await _collect(agent_mod.astream_message("t1", "안녕", graph=graph))
    names = [e["event"] for e in events]

    assert names[0] == "run_started"
    assert names[-1] == "run_finished"
    assert "message_chunk" in names
    assert events[-1]["data"]["status"] == "completed"


async def test_stream_emits_interrupt():
    def _node(state):  # noqa: ANN001, ANN202, ARG001
        interrupt({"type": "analysis_review", "analysis": {"topic": "x"}})
        return {"messages": []}

    builder = StateGraph(MessagesState)
    builder.add_node("n", _node)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)
    graph = builder.compile(checkpointer=MemorySaver())

    events = await _collect(agent_mod._astream_turn(graph, "t2", {"messages": []}))
    names = [e["event"] for e in events]

    assert "interrupt" in names
    assert events[-1]["event"] == "run_finished"
    assert events[-1]["data"]["status"] == "interrupted"


async def test_stream_reports_error_as_event():
    # content 없이 tool_calls만 있는 응답 → 가짜 모델 스트림 생성 실패 → run_error로 전달
    bad = AIMessage(
        content="",
        tool_calls=[{"name": "analyze_passage_tool", "args": {}, "id": "c1"}],
    )
    model = _FakeToolModel(messages=iter([bad]))
    graph = agent_mod.build_writing_agent(model=model, checkpointer=MemorySaver())

    events = await _collect(agent_mod.astream_message("t3", "분석", graph=graph))
    assert events[0]["event"] == "run_started"
    assert events[-1]["event"] == "run_error"
