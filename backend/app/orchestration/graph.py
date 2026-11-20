
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

from ..config import settings
from ..agents.agent_factory import run_agent, stream_agent
from ..orchestration.state import AgentState
from ..orchestration.classifier import classify_query


# =====================================================
# CLASSIFICATION
# =====================================================

def classify_node(state: AgentState):
    """Normal classification without streaming."""

    query = state["query"]

    agent, confidence = classify_query(query)

    if confidence < settings.ROUTING_CONFIDENCE_THRESHOLD:
        agent = "general"

    return {
        "selected_agent": agent,
        "routing_confidence": confidence
    }


def classify_stream_node(state: AgentState):
    """Classification that also emits a routing event."""

    result = classify_node(state)

    writer = get_stream_writer()

    writer({
        "type": "routing",
        "agent": result["selected_agent"],
        "confidence": result["routing_confidence"]
    })

    return result


# =====================================================
# NORMAL AGENT EXECUTION
# =====================================================

def execute_agent_node(state: AgentState):

    agent_name = state["selected_agent"]
    query = state["query"]

    try:
        result = run_agent(agent_name, query)

        response_text = result.content

        if not isinstance(response_text, str):
            response_text = str(response_text)

        usage = result.usage_metadata or {}

        token_usage = {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens")
        }

        return {
            "response": response_text,
            "model_name": settings.OLLAMA_MODEL,
            "token_usage": token_usage,
            "error": ""
        }

    except Exception as exc:
        return {
            "response": "",
            "model_name": settings.OLLAMA_MODEL,
            "token_usage": {},
            "error": str(exc)
        }


# =====================================================
# STREAMING AGENT EXECUTION
# =====================================================

def execute_agent_stream_node(state: AgentState):

    agent_name = state["selected_agent"]
    query = state["query"]

    writer = get_stream_writer()

    try:
        final_result = None

        print(f"[STREAM] Starting agent: {agent_name}")

        for event in stream_agent(agent_name, query):

            if event["type"] == "token":
                writer(event)

            elif event["type"] == "done":
                final_result = event

        if final_result is None:
            raise RuntimeError(
                "Agent did not produce a final response."
            )

        writer({
            "type": "complete",
            "agent": agent_name,
            "response": final_result["response"],
            "generation_time_ms": final_result["generation_time_ms"],
            "first_token_ms": final_result["first_token_ms"],
            "total_tokens": final_result["total_tokens"],
            "finish_reason": final_result["finish_reason"],
            "prompt_tokens": final_result["prompt_tokens"],
            "completion_tokens": final_result["completion_tokens"],
            "continuation_attempts": final_result["continuation_attempts"],
            "model_name": settings.OLLAMA_MODEL
        })

        print("[STREAM] Agent completed successfully.")

        return {
            "response": final_result["response"],
            "model_name": settings.OLLAMA_MODEL,
            "token_usage": {
                "prompt_tokens": final_result["prompt_tokens"],
                "completion_tokens": final_result["completion_tokens"],
                "total_tokens": final_result["total_tokens"]
            },
            "error": ""
        }

    except Exception as exc:

        print(f"[STREAM ERROR] {exc}")

        writer({
            "type": "error",
            "message": str(exc)
        })

        return {
            "response": "",
            "model_name": settings.OLLAMA_MODEL,
            "token_usage": {},
            "error": str(exc)
        }


# =====================================================
# GRAPH BUILDER
# =====================================================

def build_agent_graph(streaming=False):

    workflow = StateGraph(AgentState)

    if streaming:
        workflow.add_node("classify", classify_stream_node)
        workflow.add_node(
            "execute_agent",
            execute_agent_stream_node
        )
    else:
        workflow.add_node("classify", classify_node)
        workflow.add_node(
            "execute_agent",
            execute_agent_node
        )

    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "execute_agent")
    workflow.add_edge("execute_agent", END)

    return workflow.compile()


# =====================================================
# GRAPH INSTANCES
# =====================================================

agent_graph = build_agent_graph()
streaming_agent_graph = build_agent_graph(streaming=True)


# =====================================================
# NORMAL EXECUTION
# =====================================================

def process_query(query: str):

    return agent_graph.invoke({
        "query": query
    })


# =====================================================
# STREAMING EXECUTION
# =====================================================


def process_query_stream(query: str):
    """
    Yields custom streaming events from LangGraph.
    """

    for event in streaming_agent_graph.stream(
        {"query": query},
        stream_mode="custom"
    ):
        yield event
