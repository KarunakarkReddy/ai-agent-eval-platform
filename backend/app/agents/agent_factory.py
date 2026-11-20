
import time
from functools import lru_cache

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from ..config import settings
from ..agents.prompts import AGENT_PROMPTS


# =====================================================
# LLM CONFIGURATION
# =====================================================

@lru_cache(maxsize=1)
def get_llm():

    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        num_predict=1024,
        num_ctx=4096,
        keep_alive="10m",
        streaming=True
    )


# =====================================================
# AGENT CHAIN
# =====================================================

@lru_cache(maxsize=4)
def get_agent_chain(agent_name: str):

    if agent_name not in AGENT_PROMPTS:
        raise ValueError(f"Unknown agent: {agent_name}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_PROMPTS[agent_name]),
        ("human", "{query}")
    ])

    return prompt | get_llm()


# =====================================================
# STREAMING AGENT EXECUTION
# =====================================================

def stream_agent(agent_name: str, query: str):
    """
    Streams the agent response progressively.

    Events:
      token: generated text
      done: final response and performance metrics
    """

    llm = get_llm()
    chain = get_agent_chain(agent_name)

    start_time = time.perf_counter()
    first_token_time = None

    full_answer = ""

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    finish_reason = None
    attempts = 0
    max_attempts = 2

    current_stream = chain.stream({
        "query": query
    })

    # =================================================
    # GENERATION LOOP
    # =================================================

    while True:

        # Usage counters for this generation attempt.
        attempt_prompt_tokens = 0
        attempt_completion_tokens = 0
        attempt_total_tokens = 0

        for chunk in current_stream:

            # Read metadata BEFORE checking text content.
            usage = chunk.usage_metadata or {}
            metadata = chunk.response_metadata or {}

            # LangChain usage metadata.
            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0
            usage_total = usage.get("total_tokens", 0) or 0

            # Ollama response metadata.
            ollama_prompt = metadata.get(
                "prompt_eval_count", 0
            ) or 0

            ollama_output = metadata.get(
                "eval_count", 0
            ) or 0

            # Keep the highest cumulative count within
            # this generation attempt.
            attempt_prompt_tokens = max(
                attempt_prompt_tokens,
                input_tokens,
                ollama_prompt
            )

            attempt_completion_tokens = max(
                attempt_completion_tokens,
                output_tokens,
                ollama_output
            )

            attempt_total_tokens = max(
                attempt_total_tokens,
                usage_total,
                attempt_prompt_tokens + attempt_completion_tokens
            )

            # Capture finish reason.
            reason = (
                metadata.get("done_reason")
                or metadata.get("finish_reason")
            )

            if reason:
                finish_reason = reason

            # Process generated text.
            content = chunk.content

            if isinstance(content, str) and content:

                if first_token_time is None:
                    first_token_time = time.perf_counter()

                full_answer += content

                yield {
                    "type": "token",
                    "content": content
                }

        # Add this attempt's usage to the totals.
        total_prompt_tokens += attempt_prompt_tokens
        total_completion_tokens += attempt_completion_tokens

        total_tokens += max(
            attempt_total_tokens,
            attempt_prompt_tokens + attempt_completion_tokens
        )

        # Continue only if Ollama reached its token limit.
        if finish_reason != "length" or attempts >= max_attempts:
            break

        attempts += 1

        continuation_prompt = f"""
The original question was:
{query}

Your previous answer:
{full_answer}

Continue exactly where the previous answer stopped.
Do not repeat previous content.
Complete all remaining sections and finish the answer properly.
"""

        current_stream = llm.stream(continuation_prompt)

        finish_reason = None

    # =================================================
    # PERFORMANCE METRICS
    # =================================================

    end_time = time.perf_counter()

    total_time_ms = round(
        (end_time - start_time) * 1000,
        2
    )

    first_token_ms = (
        round(
            (first_token_time - start_time) * 1000,
            2
        )
        if first_token_time is not None
        else None
    )

    print("\n========== OLLAMA STREAMING PERFORMANCE ==========")
    print("Agent:", agent_name)
    print("First token:", first_token_ms, "ms")
    print("Generation time:", total_time_ms, "ms")
    print("Prompt tokens:", total_prompt_tokens)
    print("Completion tokens:", total_completion_tokens)
    print("Total tokens:", total_tokens)
    print("Finish reason:", finish_reason)
    print("Continuation attempts:", attempts)
    print("===================================================\n")

    # =================================================
    # FINAL EVENT
    # =================================================

    yield {
        "type": "done",
        "response": full_answer,
        "generation_time_ms": total_time_ms,
        "first_token_ms": first_token_ms,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "finish_reason": finish_reason,
        "continuation_attempts": attempts
    }


# =====================================================
# NON-STREAMING COMPATIBILITY
# =====================================================

def run_agent(agent_name: str, query: str):
    """
    Non-streaming compatibility wrapper.

    Existing callers can continue using run_agent().
    """

    final_event = None

    for event in stream_agent(agent_name, query):

        if event["type"] == "done":
            final_event = event

    if final_event is None:
        raise RuntimeError(
            "Agent did not produce a response."
        )

    return AIMessage(
        content=final_event["response"],

        usage_metadata={
            "input_tokens": final_event["prompt_tokens"],
            "output_tokens": final_event["completion_tokens"],
            "total_tokens": final_event["total_tokens"]
        },

        response_metadata={
            "done_reason": final_event["finish_reason"],
            "generation_time_ms": final_event["generation_time_ms"],
            "first_token_ms": final_event["first_token_ms"],
            "continuation_attempts": final_event["continuation_attempts"]
        }
    )
