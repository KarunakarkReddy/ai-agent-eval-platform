
from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000
    )


class ChatResponse(BaseModel):
    request_id: str
    query: str
    agent: str
    response: str
    routing_confidence: float
    model: str
    status: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    application: str
    model: str


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    user_query: str
    selected_agent: str
    model_name: str
    status: str
    latency_ms: float | None = None
