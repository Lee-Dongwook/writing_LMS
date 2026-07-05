import json
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Protocol, runtime_checkable
from unittest.mock import Mock
from uuid import uuid4

from langchain_core.load.dump import dumps
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    AnyMessage,
    ChatMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command


logger = logging.getLogger(__name__)

@runtime_checkable
class PipelineHandler(Protocol):
    """
    Protocol defining the interface for pipeline lifecycle handling.
    """

    async def on_completion(
        self,
        final_state: dict,
        thread_id: str,
        user_uuid: str,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        """Called when the pipeline finishes or interrupts."""
        ...

class BasicPipeline(PipelineHandler):
    async def on_completion(
        self,
        final_state: dict,
        thread_id: str,
        user_uuid: str,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        if not (isinstance(checkpointer, AsyncPostgresSaver) and final_state.get("messages")):
            return
        last_message_id = None
        async with async_context_session() as db:
            thread = await select_thread_by_uuid(db, thread_id)
            if thread is None:
                title_message = final_state["messages"][0].content or "New Thread"
                try:
                    thread = await create_new_thread(user_uuid, title_message, thread_id, db)
                except Exception as e:
                    logger.error(f"Fail to create thread: {e}")

            if thread is None:
                logger.warning("Fail to create thread")
                return

            last_saved_message = await select_last_message_in_thread(db, thread_id)
            if last_saved_message and "data" in last_saved_message.message:
                last_message_id = last_saved_message.message["data"]["id"]

            filtered_messages = _filterout_toolmessages(final_state["messages"], last_message_id)
            logger.info(f"Total length of the saved messages = {len(filtered_messages)}")

            conn = getattr(checkpointer, "conn", None)
            if conn:
                await _save_message(filtered_messages, thread_id, conn)

_PIPELINE_GRAPH_CACHE = {}


def _create_node_function(step: SimpleStep) -> Callable:
    async def _node_wrapper(state: AgentState, config: RunnableConfig) -> dict:
        logger.info(f"--- Executing Step Node: {step.name} ---")
        action = step.action

        # Mock agent model needed for executors
        mock_agent = Mock()
        mock_agent.tools = []

        # reset error!!
        state["values"]["error"] = None
        try:
            if action.action_type == "llm_call":
                result = await execute_llm_call(action, state, config)
                return {"values": {action.output_key: result}}
            elif action.action_type == "tool_call":
                result = await execute_tool_call(action, state, agent_model=mock_agent, config=config)
                return {"values": {action.output_key: result}}
            elif action.action_type == "agent_call":
                user_uuid = config.get("configurable", {}).get("user_uuid") if config else None
                resolver = DefaultSubAgentResolver()
                resolved = await resolver.resolve({action.agent_slug}, user_uuid=user_uuid)
                sub_agent_model = resolved.get(action.agent_slug)
                if not sub_agent_model:
                    raise ValueError(f"Sub-agent '{action.agent_slug}' not found or is disabled.")
                return await execute_agent_call(
                    action, state, config, sub_agent_model=sub_agent_model, resolver=resolver
                )
            else:
                raise NotImplementedError(f"Action type '{action.action_type}' not supported.")
        except Exception as e:
            error_content = f"Error in step '{step.name}': {e}"
            logger.error(error_content)
            # Errors are typically captured in the state or handled by downstream nodes.
            # but in this case, we should raise the error to pinpoint real cause of raise
            raise e

    return _node_wrapper


def _create_graph_from_pipeline(unique: str, pipeline: PipeLine) -> CompiledStateGraph:
    """
    Dynamically builds a linear StateGraph from a PipeLine schema.
    The graph is cached for performance.
    """

    # Create a unique key for the pipeline structure for caching
    pipeline_structure_key = str(unique) + "-".join([s.name for s in pipeline.steps])
    if pipeline_structure_key in _PIPELINE_GRAPH_CACHE:
        logger.info("✈️ Cached graph served")
        return _PIPELINE_GRAPH_CACHE[pipeline_structure_key]

    graph = StateGraph(AgentState, GraphConfig)

    # Add nodes for each step
    for step in pipeline.steps:
        graph.add_node(step.name, _create_node_function(step))

    # Add edges to connect nodes in a linear sequence
    if pipeline.steps:
        graph.set_entry_point(pipeline.steps[0].name)
        for i in range(len(pipeline.steps) - 1):
            graph.add_edge(pipeline.steps[i].name, pipeline.steps[i+1].name)
        # Add an edge from the last step to the end
        graph.add_edge(pipeline.steps[-1].name, END)
    else: # No steps, just start and end
        graph.set_entry_point(END) # In an empty pipeline, it finishes immediately

    if len(pipeline.steps) > 1:
        # --- Set interrupt after every step ---
        interrupt_nodes = [step.name for step in pipeline.steps[:-1]]
        compiled_graph = graph.compile(name="doc_template_pipeline", interrupt_after=interrupt_nodes)
    else:
        # no interrupts for 1 step pipeline
        compiled_graph = graph.compile(name="doc_template_pipeline")

    _PIPELINE_GRAPH_CACHE[pipeline_structure_key] = compiled_graph
    return compiled_graph


def _prepare_payload_for_agent(payload: Any) -> Any:
    """
    Recursively processes the payload to replace FileInfo dicts with their file_url strings.
    Agents expect direct file paths/URLs, not full FileInfo objects.
    """
    if isinstance(payload, dict):
        # Check if it looks like a FileInfo object (has 'file_url')
        if "file_url" in payload and isinstance(payload["file_url"], str):
            return payload["file_url"]

        # Otherwise, recurse into the dict
        return {k: _prepare_payload_for_agent(v) for k, v in payload.items()}

    elif isinstance(payload, list):
        return [_prepare_payload_for_agent(item) for item in payload]

    return payload

async def run_pipeline(
    unique: str,
    pipeline: PipeLine,
    user_uuid: str,
    payload: dict | None = None,
    thread_uuid: str | None = None,
    streaming: bool = False,
    protocol: str = "legacy",
    checkpointer: BaseCheckpointSaver | None = None,
    handler: PipelineHandler | None = None,
) -> AsyncGenerator[str | dict]:
    """
    Initializes (if new) and runs a pipeline graph to completion.
    Leverages LangGraph's checkpointing for automatic state management and resume.
    """
    thread_id = thread_uuid or str(uuid4())

    # Pre-process payload to convert FileInfo to file_url strings
    if payload:
        cleaned_payload = _prepare_payload_for_agent(payload)
    else:
        cleaned_payload = {}

    active_handler = handler or DefaultPipelineHandler()

    @asynccontextmanager
    async def _wrap_checkpointer(
        checkpointer: BaseCheckpointSaver | None,
    ) -> AsyncGenerator[BaseCheckpointSaver | None]:
        yield checkpointer

    async with _wrap_checkpointer(checkpointer) as cp:
        configurable = dict(
            search_model_temperature=0.7,
            guide_disable_streaming=True,
            category_disable_streaming=True,
            critique_disable_streaming=True,
            thread_id=thread_id,
            checkpoint_ns="",
            user_uuid=user_uuid,
        )

        config = GraphConfig(
            thread_id=thread_id,
            recursion_limit=25,
            configurable=configurable,
        )

        pipeline_graph = _create_graph_from_pipeline(unique, pipeline)
        if cp:
            pipeline_graph.checkpointer = cp

        initial_state = {
            "values": cleaned_payload,
            "user_uuid": user_uuid,
            "messages": [],
        }

        # --- Check for interrupts ---
        # Get the current persisted state from the checkpointer
        current_snapshot = None
        if thread_uuid:
            logger.info(f"thread_uuid = {thread_uuid}")
            current_snapshot = await pipeline_graph.aget_state(config)

        resume = None
        if current_snapshot and current_snapshot.interrupts:
            logger.info(f"{thread_uuid} was interrupted")
            resume = Command(resume=True)
        elif current_snapshot and current_snapshot.next:
            resume = Command(resume=True)
            logger.info(f"{thread_uuid} was interrupted at {current_snapshot.next}")

        current_state = current_snapshot.values if current_snapshot else None

        # Apply input mapping if defined
        if pipeline.input_mapping and cleaned_payload:
            mapped_payload = {}

            for pipeline_key, payload_key in pipeline.input_mapping.items():
                # 1. Try to get value directly from state using the mapping key
                if payload_key in cleaned_payload:
                    mapped_payload[pipeline_key] = cleaned_payload[payload_key]
                else:
                    # 2. If key not found, treat as literal or template
                    mapped_payload[pipeline_key] = resolve_template(payload_key, current_state or initial_state, config)

            # Merge mapped payload with original payload to keep unmapped fields
            # Mapped values take precedence if keys collide (though they shouldn't usually)
            final_payload = {**cleaned_payload, **mapped_payload}

            # updated inital_state
            initial_state = {
                "values": final_payload,
                "messages": [],
            }
        else:
            final_payload = cleaned_payload

        # check updated payload
        if current_state and cleaned_payload:
            # to update interrupted step with newly updated payload
            await pipeline_graph.aupdate_state(config=config, values=initial_state)

        try:
            if streaming:
                internal_gen = _with_heartbeat(
                    astream_graph(
                        graph=pipeline_graph,
                        initial_state=resume if resume else initial_state,
                        thread_uuid=thread_id,
                        config=config,
                    ),
                    thread_uuid=thread_id,
                )

                # Select wrapper based on protocol
                wrapper = ag_ui_wrapper if protocol == "ag-ui" else legacy_sse_wrapper

                async for chunk in wrapper(internal_gen):
                    yield chunk

            else:
                # ainvoke will automatically resume from the last checkpoint if the thread_id exists
                final_state = await pipeline_graph.ainvoke(resume if resume else initial_state, config=config)
                #final_values = final_state.get("values", {})

        except Exception as e:
            error_content = f"Error: exception from pipeline: {e}"
            logger.error(error_content, exc_info=True)
            # Yield error in protocol-compatible way if needed
            # For now, keeping legacy error dict for non-streaming compatibility
            yield {
                "status": "pipeline_failed",
                "message": error_content,
                "thread_uuid": thread_id,
                "error_details": str(e),
            }

        # get the `final_snapshot` again
        # we can use `final_state["messages"]` to get the messages here.
        # but when we ready to use graph.astream(...), we have to use aget_state(config) here.
        final_snapshot = await pipeline_graph.aget_state(config)
        final_state = final_snapshot.values if final_snapshot else {}
        final_values = final_state.get("values", {})

        # --- Check for errors ---
        if final_values.get("error"):
             yield {
                "status": "pipeline_failed",
                "message": f"Pipeline failed to execute. Error: {final_values['error']}",
                "thread_uuid": thread_id,
                "error_details": final_values["error"],
                "final_state": final_values,
             }

        # Execute completion handler
        await active_handler.on_completion(final_state, thread_id, user_uuid, cp)

        if final_snapshot and final_snapshot.next:
            # Pipeline is interrupted (paused)
            yield {
                "status": "pipeline_interrupted",
                "message": "Pipeline interrupted. Waiting for resume.",
                "thread_uuid": thread_id,
                "current_state": final_values,
                "next_node_names": final_snapshot.next,
            }
        else:
            # Pipeline is completed
            yield {
                "status": "pipeline_completed",
                "message": "Pipeline executed successfully.",
                "thread_uuid": thread_id,
                "final_state": final_values,
            }


async def _event_from_message(
    last_ai_message: AnyMessage,
    final_state: AgentState,
    thread_uuid: str,
    chunktype: str = "complete",
) -> dict[str, Any]:
    """Check the last ai message and return internal event data (snake_case)."""
    ai_content = last_ai_message.content

    final_event = {
        "type": chunktype,
        "thread_uuid": thread_uuid,
        "id": last_ai_message.id,
        "data": {
            "type": "ai",
            "content": ai_content,
        },
    }

    return final_event


async def astream_graph(
    graph: CompiledStateGraph,
    initial_state: dict,
    thread_uuid: str,
    config: GraphConfig,
) -> AsyncGenerator[dict[str, Any]]:
    """
    Streams internal standard events from the pipeline graph.
    """

    _persisted_state = await graph.aget_state(config)

    last_message_id = None
    # get the last saved human message's msg.id
    if _persisted_state and "messages" in _persisted_state.values:
        # get the last `filtered` saved message to get the last_message_id
        async with async_context_session() as db:
            last_saved_message = await select_last_message_in_thread(db, thread_uuid)
            if last_saved_message:
                last_message_id = last_saved_message.message["data"]["id"]

    last_ai_message = None
    final_state = None

    message_dict = {}
    # If it is a pipeline graph, we can try to find steps from its nodes
    if hasattr(graph, 'nodes'):
        message_dict = {
            node_name: node_name
            for node_name in graph.nodes
            if node_name not in ["__start__", "__end__"]
        }

    # Signal start
    yield {
        "event": "run_started",
        "metadata": {
            "thread_uuid": thread_uuid,
            "timestamp": int(time.time() * 1000),
        },
    }

    try:
        async for chunk in graph.astream(
            input=initial_state,
            config=config,
            stream_mode=["updates", "messages", "custom"],
            subgraphs=True,
        ):
            _ns = mode = None
            if isinstance(chunk, tuple):
                if len(chunk) == 3:
                    _ns, mode, chunk = chunk
                else:
                    dummy, chunk = chunk
                    if dummy in ["updates", "messages", "custom"]:
                        mode = dummy
                    else:
                        _ns = dummy

            if mode not in ["updates"]:
                if mode == "messages":
                    # ignore some subgraph's chunk messages
                    # check namespaces e.g.) ('link_subgraph:xxxxxxxx-....', 'link_process_subgraph:yyyyyyyy-...',
                    #if ns and ns[0].split(":")[0] in ["link_subgraph"]:
                    #    continue

                    for message in chunk:
                        #if isinstance(message, AIMessageChunk | ChatMessageChunk):
                        if isinstance(message, AIMessageChunk):
                            if not message.content: # ignore empty chunk
                                continue

                            yield {
                                "event": "message_chunk",
                                "data": {
                                    "content": message.content,
                                    "message_id": message.id,
                                },
                                "metadata": {
                                    "thread_uuid": thread_uuid,
                                    "timestamp": int(time.time() * 1000),
                                },
                            }
                    continue

                if mode == "custom":
                    logger.debug(f"TODO MESSAGES TYPE = {type(chunk)}, MESSAGES = {dumps(chunk, pretty=True, ensure_ascii=False)}")
                    yield {
                        "event": "custom",
                        "data": chunk,
                        "metadata": {
                            "thread_uuid": thread_uuid,
                            "timestamp": int(time.time() * 1000),
                        },
                    }
                    continue

                continue

            for node_name, node_output in chunk.items():
                if node_name in ["del_tool_call"]:
                    continue

                if node_name in message_dict.keys():
                    routing_info = node_output.get("routing_info", node_name) if node_output else node_name
                    logger.debug(f"routing_info or node_name = {routing_info}")
                    msg_id = node_output["messages"][-1].id if node_output and "messages" in node_output else None

                    yield {
                        "event": "step_started",
                        "data": {
                            "node_name": node_name,
                            "status_message": message_dict.get(routing_info, message_dict[node_name]),
                            "message_id": msg_id,
                        },
                        "metadata": {
                            "thread_uuid": thread_uuid,
                            "timestamp": int(time.time() * 1000),
                        },
                    }
                elif node_name == "__interrupt__":
                    # check human-in-the-loop interrupt events
                    if not node_output:
                        continue

                    try:
                        msg = node_output[0].value
                    except (IndexError, AttributeError, TypeError) as e:
                        logger.error("Fail to parse human-in-the-loop message", exc_info=True)
                        raise

                    if msg.content:
                        yield {
                            "event": "interrupt",
                            "data": {"content": msg.content, "message_id": msg.id},
                            "metadata": {
                                "thread_uuid": thread_uuid,
                                "timestamp": int(time.time() * 1000),
                            },
                        }


                if isinstance(node_output, dict) and "messages" in node_output:
                    final_state = node_output
                    for msg in reversed(node_output["messages"]):
                        # check the latest AIMessage.
                        if hasattr(msg, "id") and last_message_id and last_message_id == msg.id:
                            # this is the last saved HumanMessage.
                            break

                        # check the agent's output AIMessage.
                        # use node_name ends with "*_subgraph"
                        if isinstance(msg, AIMessage):
                        #if isinstance(msg, AIMessage | ChatMessage):
                            last_ai_message = msg
                            if node_name.endswith("_subgraph"):
                                event_data = await _event_from_message(msg, node_output, thread_uuid, "message")
                                yield {
                                    "event": "message_complete",
                                    "data": {**event_data["data"], "message_id": msg.id, "chunktype": "message"},
                                    "metadata": {
                                        "thread_uuid": thread_uuid,
                                        "timestamp": int(time.time() * 1000),
                                    },
                                }
                            break

        if last_ai_message:
            final_event_data = await _event_from_message(last_ai_message, final_state, thread_uuid)
            yield {
                "event": "run_finished",
                "data": {**final_event_data["data"], "message_id": last_ai_message.id, "chunktype": "complete"},
                "metadata": {
                    "thread_uuid": thread_uuid,
                    "timestamp": int(time.time() * 1000),
                },
            }
        else:
            yield {
                "event": "run_finished",
                "metadata": {
                    "thread_uuid": thread_uuid,
                    "timestamp": int(time.time() * 1000),
                },
            }

    except Exception as e:
        logger.error(f"Error in astream_graph: {e}", exc_info=True)
        yield {
            "event": "run_error",
            "data": {"message": str(e)},
            "metadata": {
                "thread_uuid": thread_uuid,
                "timestamp": int(time.time() * 1000),
            },
        }
