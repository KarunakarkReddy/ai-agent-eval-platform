
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def current_utc_time():
    return datetime.now(timezone.utc)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    request_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    user_query: Mapped[str] = mapped_column(Text)
    selected_agent: Mapped[str] = mapped_column(String(100))
    routing_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    model_name: Mapped[str] = mapped_column(String(100))
    response: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="success"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    latency_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=current_utc_time
    )


class LLMMetric(Base):
    __tablename__ = "llm_metrics"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"), index=True
    )
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    total_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    latency_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=current_utc_time
    )


class AgentEvaluation(Base):
    __tablename__ = "agent_evaluations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"), index=True
    )
    metric_name: Mapped[str] = mapped_column(String(100))
    score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=current_utc_time
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    __table_args__ = (
        UniqueConstraint(
            "agent_name",
            "version",
            name="uq_agent_prompt_version"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=current_utc_time
    )
