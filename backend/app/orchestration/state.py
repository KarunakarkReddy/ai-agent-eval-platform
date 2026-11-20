
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    selected_agent: str
    routing_confidence: float
    response: str
    model_name: str
    token_usage: dict[str, Any]
    error: str
