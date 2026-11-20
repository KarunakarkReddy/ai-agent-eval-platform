
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..models import AgentRun, LLMMetric


def log_agent_execution(
    db: Session,
    request_id: str,
    query: str,
    result: dict,
    latency_ms: float,
    status: str = "success",
    error_message: str | None = None
):
    """Save an agent execution and its token metrics."""

    agent_run = AgentRun(
        request_id=request_id,
        user_query=query,
        selected_agent=result.get("selected_agent", "general"),
        routing_confidence=result.get("routing_confidence", 0.0),
        model_name=result.get("model_name", "unknown"),
        response=result.get("response"),
        status=status,
        error_message=error_message,
        latency_ms=latency_ms
    )

    try:
        db.add(agent_run)
        db.flush()

        token_usage = result.get("token_usage") or {}

        metric = LLMMetric(
            agent_run_id=agent_run.id,
            prompt_tokens=token_usage.get("prompt_tokens"),
            completion_tokens=token_usage.get("completion_tokens"),
            total_tokens=token_usage.get("total_tokens"),
            latency_ms=latency_ms
        )

        db.add(metric)
        db.commit()
        db.refresh(agent_run)

        return agent_run

    except Exception:
        db.rollback()
        raise


def get_recent_runs(db: Session, limit: int = 50):
    """Return the latest agent executions."""

    return (
        db.query(AgentRun)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
        .all()
    )


def get_monitoring_summary(db: Session):
    """Calculate overall and agent-wise LLMOps statistics."""

    total_requests = (
        db.query(func.count(AgentRun.id)).scalar() or 0
    )

    successful_requests = (
        db.query(func.count(AgentRun.id))
        .filter(AgentRun.status == "success")
        .scalar() or 0
    )

    failed_requests = (
        db.query(func.count(AgentRun.id))
        .filter(AgentRun.status == "failed")
        .scalar() or 0
    )

    average_latency = (
        db.query(func.avg(AgentRun.latency_ms))
        .filter(AgentRun.latency_ms.isnot(None))
        .scalar()
    )

    total_tokens = (
        db.query(func.sum(LLMMetric.total_tokens)).scalar() or 0
    )

    agent_distribution = (
        db.query(
            AgentRun.selected_agent,
            func.count(AgentRun.id)
        )
        .group_by(AgentRun.selected_agent)
        .all()
    )

    # Agent-wise performance statistics
    agent_rows = (
        db.query(
            AgentRun.selected_agent,
            func.count(AgentRun.id).label("total_requests"),
            func.sum(
                case(
                    (AgentRun.status == "success", 1),
                    else_=0
                )
            ).label("successful_requests"),
            func.sum(
                case(
                    (AgentRun.status == "failed", 1),
                    else_=0
                )
            ).label("failed_requests"),
            func.avg(AgentRun.latency_ms).label("average_latency_ms"),
            func.sum(LLMMetric.total_tokens).label("total_tokens")
        )
        .outerjoin(
            LLMMetric,
            LLMMetric.agent_run_id == AgentRun.id
        )
        .group_by(AgentRun.selected_agent)
        .all()
    )

    agent_performance = {}

    for row in agent_rows:
        agent_performance[row.selected_agent] = {
            "total_requests": int(row.total_requests or 0),
            "successful_requests": int(row.successful_requests or 0),
            "failed_requests": int(row.failed_requests or 0),
            "average_latency_ms": round(
                float(row.average_latency_ms or 0), 2
            ),
            "total_tokens": int(row.total_tokens or 0)
        }

    success_rate = (
        successful_requests / total_requests * 100
        if total_requests else 0
    )

    failure_rate = (
        failed_requests / total_requests * 100
        if total_requests else 0
    )

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": round(success_rate, 2),
        "failure_rate": round(failure_rate, 2),
        "average_latency_ms": round(
            float(average_latency or 0), 2
        ),
        "total_tokens": int(total_tokens),
        "agent_distribution": {
            agent: count
            for agent, count in agent_distribution
        },
        "agent_performance": agent_performance
    }
