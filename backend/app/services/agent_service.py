
import time
import uuid

from sqlalchemy.orm import Session

from ..config import settings
from ..orchestration.graph import process_query, process_query_stream
from ..monitoring.logger import log_agent_execution
from ..schemas import ChatResponse


def execute_user_query(query: str, db: Session) -> ChatResponse:
    """
    Existing non-streaming execution.
    Kept for backward compatibility.
    """

    request_id = str(uuid.uuid4())
    total_start = time.perf_counter()

    result = {
        "selected_agent": "general",
        "routing_confidence": 0.0,
        "model_name": settings.OLLAMA_MODEL,
        "response": "",
        "token_usage": {}
    }

    try:
        graph_start = time.perf_counter()
        result = process_query(query)

        graph_time = (
            time.perf_counter() - graph_start
        ) * 1000

        if result.get("error"):
            raise RuntimeError(result["error"])

        logging_start = time.perf_counter()

        log_agent_execution(
            db=db,
            request_id=request_id,
            query=query,
            result=result,
            latency_ms=round(graph_time, 2),
            status="success"
        )

        logging_time = (
            time.perf_counter() - logging_start
        ) * 1000

        total_time = (
            time.perf_counter() - total_start
        ) * 1000

        print("\n========== APPLICATION PERFORMANCE ==========")
        print(f"Agent: {result['selected_agent']}")
        print(f"Graph + Ollama: {graph_time:.2f} ms")
        print(f"Database logging: {logging_time:.2f} ms")
        print(f"Total service time: {total_time:.2f} ms")
        print("=============================================\n")

        return ChatResponse(
            request_id=request_id,
            query=query,
            agent=result["selected_agent"],
            response=result["response"],
            routing_confidence=result["routing_confidence"],
            model=settings.OLLAMA_MODEL,
            status="success",
            latency_ms=round(total_time, 2)
        )

    except Exception as exc:
        total_time = (
            time.perf_counter() - total_start
        ) * 1000

        try:
            db.rollback()

            log_agent_execution(
                db=db,
                request_id=request_id,
                query=query,
                result=result,
                latency_ms=round(total_time, 2),
                status="failed",
                error_message=str(exc)
            )
        except Exception as logging_error:
            print("Failed to log execution:", logging_error)

        raise RuntimeError(
            f"Agent execution failed: {exc}"
        ) from exc


def stream_user_query(query: str, db: Session):
    """
    Streaming execution service.

    Yields:
      routing: selected agent and confidence
      token: progressive response text
      complete: final response and performance metrics
      error: execution error
    """

    request_id = str(uuid.uuid4())
    total_start = time.perf_counter()

    result = {
        "selected_agent": "general",
        "routing_confidence": 0.0,
        "model_name": settings.OLLAMA_MODEL,
        "response": "",
        "token_usage": {}
    }

    final_event = None
    graph_start = time.perf_counter()
    graph_time = 0.0

    try:
        for event in process_query_stream(query):

            if event["type"] == "routing":
                result["selected_agent"] = event["agent"]
                result["routing_confidence"] = event["confidence"]

                yield {
                    "type": "routing",
                    **event
                }

            elif event["type"] == "token":
                yield event

            elif event["type"] == "complete":
                final_event = event

            elif event["type"] == "error":
                raise RuntimeError(event["message"])

        graph_time = (
            time.perf_counter() - graph_start
        ) * 1000

        if final_event is None:
            raise RuntimeError(
                "Streaming completed without a final response."
            )

        result["response"] = final_event["response"]
        result["model_name"] = settings.OLLAMA_MODEL
        result["token_usage"] = {
            "completion_tokens": final_event["total_tokens"],
            "total_tokens": final_event["total_tokens"]
        }

        # Save the completed answer to MySQL.
        logging_start = time.perf_counter()

        log_agent_execution(
            db=db,
            request_id=request_id,
            query=query,
            result=result,
            latency_ms=round(graph_time, 2),
            status="success"
        )

        logging_time = (
            time.perf_counter() - logging_start
        ) * 1000

        total_time = (
            time.perf_counter() - total_start
        ) * 1000

        print("\n========== STREAMING APPLICATION PERFORMANCE ==========")
        print(f"Request ID: {request_id}")
        print(f"Agent: {result['selected_agent']}")
        print(f"Graph + generation: {graph_time:.2f} ms")
        print(f"Database logging: {logging_time:.2f} ms")
        print(
            f"Model generation: "
            f"{final_event['generation_time_ms']:.2f} ms"
        )
        print(
            f"First token: "
            f"{final_event['first_token_ms']} ms"
        )
        print(f"Total service time: {total_time:.2f} ms")
        print("========================================================\n")

        # Send final metrics after database logging.
        yield {
            "type": "complete",
            "request_id": request_id,
            "agent": result["selected_agent"],
            "response": result["response"],
            "model": settings.OLLAMA_MODEL,
            "routing_confidence": result["routing_confidence"],
            "generation_time_ms": final_event["generation_time_ms"],
            "first_token_ms": final_event["first_token_ms"],
            "total_service_time_ms": round(total_time, 2),
            "database_logging_ms": round(logging_time, 2),
            "total_tokens": final_event["total_tokens"],
            "finish_reason": final_event["finish_reason"],
            "continuation_attempts": final_event["continuation_attempts"],
            "status": "success"
        }

    except Exception as exc:

        total_time = (
            time.perf_counter() - total_start
        ) * 1000

        try:
            db.rollback()

            log_agent_execution(
                db=db,
                request_id=request_id,
                query=query,
                result=result,
                latency_ms=round(total_time, 2),
                status="failed",
                error_message=str(exc)
            )

        except Exception as logging_error:
            print("Failed to log streaming error:", logging_error)

        yield {
            "type": "error",
            "request_id": request_id,
            "message": str(exc),
            "status": "failed"
        }
