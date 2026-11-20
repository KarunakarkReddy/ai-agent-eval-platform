
import requests
import pandas as pd
import streamlit as st
import json

# =====================================================
# CONFIGURATION
# =====================================================

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Enterprise AI Agent Platform",
    page_icon="🤖",
    layout="wide"
)


# =====================================================
# API HELPER FUNCTIONS
# =====================================================

def api_get(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"Backend connection error: {error}")
        return None


def api_post(endpoint, payload=None):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"API request failed: {error}")
        return None


def api_stream_post(endpoint, payload):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            stream=True,
            timeout=(10, 300)
        )

        response.raise_for_status()
        return response

    except requests.RequestException as error:
        st.error(f"Streaming API error: {error}")
        return None

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("🤖 Enterprise AI Platform")

page = st.sidebar.radio(
    "Navigation",
    ["AI Agent Chat", "LLMOps Monitoring"]
)

st.sidebar.divider()

health = api_get("/health")

if health:
    st.sidebar.success("Backend Connected")
else:
    st.sidebar.error("Backend Unavailable")



# =====================================================
# AI AGENT CHAT - STREAMING
# =====================================================

if page == "AI Agent Chat":

    st.title("AI Agent Assistant")

    st.caption(
        "Intelligent query routing using LangGraph "
        "and specialized AI agents."
    )

    query = st.text_area(
        "Enter your question",
        placeholder="Ask a technical, analytical, support, or general question...",
        height=120
    )

    if st.button("Submit Query", type="primary"):

        if not query.strip():
            st.warning("Please enter a question.")

        else:

            full_response = ""
            final_result = None
            selected_agent = "Detecting..."
            routing_confidence = 0.0

            response_placeholder = st.empty()
            status_placeholder = st.empty()
            metrics_placeholder = st.empty()

            status_placeholder.info("Connecting to AI agent...")

            response = api_stream_post(
                "/chat/stream",
                {"query": query}
            )

            if response:

                try:
                    with response:

                        for line in response.iter_lines(
                            decode_unicode=True
                        ):

                            if not line or not line.startswith("data:"):
                                continue

                            event = json.loads(
                                line[len("data:"):].strip()
                            )

                            event_type = event.get("type")

                            # Agent routing information
                            if event_type == "routing":

                                selected_agent = event.get(
                                    "agent", "general"
                                )

                                routing_confidence = event.get(
                                    "confidence", 0.0
                                )

                                status_placeholder.info(
                                    f"Selected Agent: {selected_agent.title()} | "
                                    "Generating response..."
                                )

                            # Display generated text progressively
                            elif event_type == "token":

                                full_response += event.get(
                                    "content", ""
                                )

                                response_placeholder.markdown(
                                    full_response + "▌"
                                )

                            # Final response and metrics
                            elif event_type == "complete":

                                final_result = event

                            elif event_type == "error":

                                status_placeholder.error(
                                    event.get(
                                        "message",
                                        "Agent execution failed."
                                    )
                                )

                    if final_result:

                        # Remove the streaming cursor
                        full_response = final_result.get(
                            "response",
                            full_response
                        )

                        response_placeholder.markdown(
                            full_response
                        )

                        status_placeholder.success(
                            "Response generated successfully!"
                        )

                        # Store result for response evaluation
                        st.session_state["last_result"] = {
                            "request_id": final_result.get("request_id"),
                            "query": query,
                            "agent": final_result.get(
                                "agent", selected_agent
                            ),
                            "response": full_response,
                            "model": final_result.get("model"),
                            "routing_confidence": final_result.get(
                                "routing_confidence",
                                routing_confidence
                            ),
                            "latency_ms": final_result.get(
                                "total_service_time_ms", 0
                            ),
                            "generation_time_ms": final_result.get(
                                "generation_time_ms", 0
                            ),
                            "first_token_ms": final_result.get(
                                "first_token_ms"
                            ),
                            "total_tokens": final_result.get(
                                "total_tokens", 0
                            ),
                            "status": final_result.get(
                                "status", "success"
                            )
                        }

                        st.subheader("Performance Metrics")

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric(
                            "Selected Agent",
                            final_result.get(
                                "agent", selected_agent
                            ).title()
                        )

                        col2.metric(
                            "Model",
                            final_result.get("model", "N/A")
                        )

                        col3.metric(
                            "Generation Time",
                            f"{final_result.get('generation_time_ms', 0) / 1000:.2f} s"
                        )

                        col4.metric(
                            "Total Tokens",
                            f"{final_result.get('total_tokens', 0):,}"
                        )

                        col1, col2, col3 = st.columns(3)

                        first_token = final_result.get(
                            "first_token_ms"
                        )

                        col1.metric(
                            "First Token Time",
                            (
                                f"{first_token / 1000:.2f} s"
                                if first_token is not None
                                else "N/A"
                            )
                        )

                        col2.metric(
                            "Total Service Time",
                            f"{final_result.get('total_service_time_ms', 0) / 1000:.2f} s"
                        )

                        col3.metric(
                            "Database Logging",
                            f"{final_result.get('database_logging_ms', 0):.2f} ms"
                        )

                        st.subheader("AI Response")

                        confidence = final_result.get(
                            "routing_confidence"
                        )

                        if confidence is not None:
                            st.caption(
                                f"Routing confidence: {confidence * 100:.1f}%"
                            )

                        st.caption(
                            f"Status: {final_result.get('status', 'success')}"
                        )

                        st.code(
                            f"Request ID: {final_result.get('request_id', 'N/A')}"
                        )

                    elif not full_response:
                        status_placeholder.warning(
                            "No response was generated."
                        )

                except Exception as error:
                    status_placeholder.error(
                        f"Error while receiving streamed response: {error}"
                    )

            else:
                status_placeholder.error(
                    "Unable to connect to streaming endpoint."
                )

    # -------------------------------------------------
    # RESPONSE EVALUATION
    # -------------------------------------------------

    if "last_result" in st.session_state:

        last_result = st.session_state["last_result"]
        request_id = last_result.get("request_id")

        if request_id:

            if st.button("Evaluate Last Response"):

                with st.spinner("Evaluating response..."):

                    evaluation = api_post(
                        f"/evaluation/{request_id}"
                    )

                if evaluation:
                    st.subheader("Evaluation Results")
                    st.json(evaluation)



# =====================================================
# LLMOPS MONITORING DASHBOARD
# =====================================================

elif page == "LLMOps Monitoring":

    st.title("LLMOps Monitoring Dashboard")

    st.caption(
        "Monitor agent execution, performance, "
        "model usage, and operational metrics."
    )

    # -------------------------------------------------
    # REFRESH BUTTON
    # -------------------------------------------------

    if st.button("🔄 Refresh Monitoring Data"):
        st.rerun()

    # -------------------------------------------------
    # FETCH MONITORING DATA
    # -------------------------------------------------

    summary = api_get("/monitoring/summary")
    runs = api_get("/monitoring/runs?limit=100")

    if summary is not None:

        st.subheader("Performance Overview")

        # Extract individual numeric metrics.
        # Dictionaries such as agent_distribution
        # must not be passed directly to st.metric().

        total_requests = summary.get("total_requests", 0)
        successful_requests = summary.get("successful_requests", 0)
        failed_requests = summary.get("failed_requests", 0)
        average_latency = summary.get("average_latency_ms", 0)
        total_tokens = summary.get("total_tokens", 0)

        average_latency = float(average_latency or 0)

        # First row of metrics

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Requests",
            total_requests
        )

        col2.metric(
            "Successful Requests",
            successful_requests
        )

        col3.metric(
            "Failed Requests",
            failed_requests
        )

        col4.metric(
            "Average Latency",
            f"{average_latency:,.2f} ms"
        )

        # Second row

        col5, col6 = st.columns(2)

        col5.metric(
            "Total Tokens",
            f"{total_tokens:,}"
        )

        success_rate = (
            (successful_requests / total_requests) * 100
            if total_requests
            else 0
        )

        col6.metric(
            "Success Rate",
            f"{success_rate:.2f}%"
        )

        # -------------------------------------------------
        # AGENT DISTRIBUTION
        # -------------------------------------------------

        st.divider()

        st.subheader("Agent Usage Distribution")

        agent_distribution = summary.get(
            "agent_distribution",
            {}
        )

        if isinstance(agent_distribution, dict) and agent_distribution:

            distribution_df = pd.DataFrame(
                list(agent_distribution.items()),
                columns=["Agent", "Requests"]
            )

            st.bar_chart(
                distribution_df.set_index("Agent")
            )

            st.dataframe(
                distribution_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No agent distribution data available.")

        
        
        # -------------------------------------------------
        # AGENT PERFORMANCE DASHBOARD
        # -------------------------------------------------

        st.divider()
        st.subheader("Agent Performance")


        # Overview KPI Cards
        st.markdown("### Overview")

        col1, col2, col3, col4 = st.columns(4)

        total_runs = summary.get("total_requests", 0)
        success_rate = summary.get("success_rate", 0)
        avg_latency = summary.get("average_latency_ms", 0)
        total_tokens = summary.get("total_tokens", 0)

        col1.metric("Total Runs", f"{total_runs:,}")

        col2.metric(
            "Success Rate",
            f"{success_rate:.1f}%"
        )

        col3.metric(
            "Average Latency",
            f"{avg_latency / 1000:.2f}s"
        )

        col4.metric(
            "Tokens Used",
            f"{total_tokens:,}"
        )


        agent_performance = summary.get("agent_performance", {})

        if agent_performance:

            # Prepare agent performance data
            rows = []

            for agent, stats in agent_performance.items():

                total = stats.get("total_requests", 0)
                successful = stats.get("successful_requests", 0)
                failed = stats.get("failed_requests", 0)

                success_rate = (
                    (successful / total) * 100 if total else 0
                )

                rows.append({
                    "Agent": agent.title(),
                    "Runs": total,
                    "Success": successful,
                    "Failed": failed,
                    "Success Rate": success_rate,
                    "Average Latency": stats.get(
                        "average_latency_ms", 0
                    ),
                    "Tokens": stats.get("total_tokens", 0)
                })

            performance_df = pd.DataFrame(rows)

            # Agent status cards
            st.markdown("### Agent Health")

            columns = st.columns(len(rows))

            for col, row in zip(columns, rows):

                rate = row["Success Rate"]

                if rate >= 90:
                    status = "🟢 Healthy"
                elif rate >= 75:
                    status = "🟡 Needs Attention"
                else:
                    status = "🔴 Poor Performance"

                with col:
                    with st.container(border=True):
                        st.markdown(f"**{row['Agent']}**")

                        st.metric(
                            "Success Rate",
                            f"{rate:.1f}%"
                        )

                        st.caption(
                            f"{row['Average Latency'] / 1000:.2f}s average latency"
                        )

                        st.caption(status)

            # Detailed performance table
            st.markdown("### Agent Performance Details")

            display_df = performance_df.copy()

            display_df["Success Rate"] = (
                display_df["Success Rate"].map(
                    lambda x: f"{x:.1f}%"
                )
            )

            display_df["Average Latency"] = (
                display_df["Average Latency"].map(
                    lambda x: f"{x / 1000:.2f}s"
                )
            )

            display_df["Tokens"] = display_df["Tokens"].map(
                lambda x: f"{x:,}"
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No agent performance data available.")

        # -------------------------------------------------
        # REQUEST RELIABILITY
        # -------------------------------------------------

        st.divider()
        st.subheader("Request Reliability")

        col1, col2 = st.columns(2)

        col1.metric(
            "Success Rate",
            f"{summary.get('success_rate', 0):.2f}%"
        )

        col2.metric(
            "Failure Rate",
            f"{summary.get('failure_rate', 0):.2f}%"
        )
    

        # -------------------------------------------------
        # COMPLETE SUMMARY
        # -------------------------------------------------

        with st.expander("View Complete Monitoring Summary"):
            st.json(summary)

    else:
        st.warning("Unable to load monitoring summary.")

    # =================================================
    # RECENT AGENT EXECUTIONS
    # =================================================

    st.divider()

    st.subheader("Recent Agent Executions")

    if runs is not None:

        # Support both list and dictionary responses

        if isinstance(runs, dict):
            run_data = runs.get(
                "runs",
                runs.get("data", [])
            )
        elif isinstance(runs, list):
            run_data = runs
        else:
            run_data = []

        if run_data:

            dataframe = pd.DataFrame(run_data)

            # Display request history

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True
            )

            # ---------------------------------------------
            # AGENT FILTER
            # ---------------------------------------------

            if "selected_agent" in dataframe.columns:

                agents = sorted(
                    dataframe["selected_agent"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                selected_agents = st.multiselect(
                    "Filter by Agent",
                    options=agents,
                    default=agents
                )

                filtered_df = dataframe[
                    dataframe["selected_agent"].isin(selected_agents)
                ]

                st.caption(
                    f"Showing {len(filtered_df)} of {len(dataframe)} executions"
                )

                # -----------------------------------------
                # LATENCY BY AGENT
                # -----------------------------------------

                if "latency_ms" in filtered_df.columns:

                    st.subheader("Latency by Agent")

                    latency_df = filtered_df.copy()

                    latency_df["latency_ms"] = pd.to_numeric(
                        latency_df["latency_ms"],
                        errors="coerce"
                    )

                    latency_by_agent = (
                        latency_df
                        .groupby("selected_agent")["latency_ms"]
                        .mean()
                    )

                    st.bar_chart(latency_by_agent)

        else:
            st.info("No agent executions found yet.")

    else:
        st.warning("Monitoring execution history is unavailable.")

    # =================================================
    # MODEL INFORMATION
    # =================================================

    st.divider()

    st.subheader("Model Configuration")

    col1, col2 = st.columns(2)

    col1.info("**Active Model:** llama3.2:3b")

    col2.info("**Orchestration:** LangGraph")
