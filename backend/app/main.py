
import json

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import AgentRun
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse
)
from .services.agent_service import (
    execute_user_query,
    stream_user_query
)
from .monitoring.logger import (
    get_recent_runs,
    get_monitoring_summary
)
from .evaluation.evaluator import evaluate_response


# Create database tables.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Agent Management and LLMOps Platform",
    version="1.0.0"
)


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Enterprise AI Agent Platform is running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    return HealthResponse(
        status="healthy",
        application=settings.APP_NAME,
        model=settings.OLLAMA_MODEL
    )


# Existing non-streaming endpoint.
@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["AI Agents"]
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        return execute_user_query(
            query=request.query,
            db=db
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# New streaming endpoint.
@app.post(
    "/chat/stream",
    tags=["AI Agents"]
)
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    def generate_events():
        for event in stream_user_query(
            query=request.query,
            db=db
        ):
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/monitoring/summary", tags=["Monitoring"])
def monitoring_summary(
    db: Session = Depends(get_db)
):
    return get_monitoring_summary(db)


@app.get("/monitoring/runs", tags=["Monitoring"])
def monitoring_runs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 500"
        )

    runs = get_recent_runs(db, limit)

    return [
        {
            "id": run.id,
            "request_id": run.request_id,
            "query": run.user_query,
            "agent": run.selected_agent,
            "confidence": run.routing_confidence,
            "model": run.model_name,
            "status": run.status,
            "latency_ms": run.latency_ms,
            "created_at": run.created_at
        }
        for run in runs
    ]


@app.post(
    "/evaluation/{request_id}",
    tags=["Evaluation"]
)
def evaluate_agent_run(
    request_id: str,
    db: Session = Depends(get_db)
):
    run = (
        db.query(AgentRun)
        .filter(AgentRun.request_id == request_id)
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Agent execution not found"
        )

    if run.status != "success" or not run.response:
        raise HTTPException(
            status_code=400,
            detail="Only successful executions can be evaluated"
        )

    try:
        results = evaluate_response(
            query=run.user_query,
            response=run.response,
            db=db,
            agent_run_id=run.id
        )

        return {
            "request_id": request_id,
            "agent": run.selected_agent,
            "evaluations": results
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {exc}"
        )
