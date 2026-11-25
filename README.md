# AI Agent Eval Platform

### AI Agent Management & LLMOps Platform

An intelligent multi-agent platform that classifies user queries, routes them to specialized AI agents, orchestrates execution using LangGraph, and evaluates AI responses using DeepEval. The platform includes real-time response streaming, performance monitoring, database persistence, and a Streamlit dashboard for interacting with agents and monitoring system performance.

---

## Overview

AI Agent Eval Platform is designed to demonstrate how an AI system can move beyond a single chatbot into a structured, observable, and evaluatable multi-agent architecture.

Instead of sending every query to the same AI model, the platform analyzes the incoming request, identifies the appropriate agent, and routes it to a specialized workflow. Each agent handles a specific category of tasks while the platform tracks execution performance and evaluates response quality.

The platform combines **AI agent orchestration, LLM evaluation, monitoring, and backend API development** into a unified application.

---

## Key Features

- **Intelligent Query Routing** – Classifies incoming queries and routes them to the appropriate specialized agent.
- **Multi-Agent Architecture** – Supports Technical, Analysis, Support, and General agents.
- **LangGraph Orchestration** – Manages agent workflow, state, routing, and execution.
- **Local LLM Integration** – Uses Ollama to run `llama3.2:3b` locally.
- **Streaming Responses** – Streams AI responses through the backend to reduce perceived waiting time.
- **Confidence-Based Routing** – Uses routing confidence and a configurable threshold to guide agent selection.
- **LLM Evaluation** – Evaluates responses using DeepEval metrics.
- **Performance Monitoring** – Tracks latency, token usage, execution performance, and agent runs.
- **Persistent Storage** – Stores execution records, LLM metrics, and evaluations in MySQL.
- **Interactive Dashboard** – Uses Streamlit for AI interaction and system monitoring.
- **REST API** – Exposes backend capabilities through FastAPI.
- **Automated Testing** – Uses Pytest for API, routing, and evaluation-related tests.

---

## Architecture
```mermaid
flowchart TD
    A["User Query"] --> B["FastAPI Backend"]
    B --> C["Query Classifier"]
    C --> D{"Query Routing"}

    D --> E["Technical Agent"]
    D --> F["Analysis Agent"]
    D --> G["Support Agent"]
    D --> H["General Agent"]

    E --> I["LangGraph Orchestration"]
    F --> I
    G --> I
    H --> I

    I --> J["Ollama LLM"]
    J --> K["llama3.2:3b"]

    K --> L["Response Generation & Streaming"]
    L --> M["Monitoring and Logging"]

    M --> N["MySQL Database"]
    M --> O["DeepEval Evaluation"]

    N --> P["Streamlit Dashboard"]
    O --> P
```

## Agent System

The platform uses specialized agents to handle different types of requests.

| Agent | Responsibility |
|---|---|
| Technical Agent | Programming, technical concepts, development, and troubleshooting |
| Analysis Agent | Analytical questions, reasoning, comparisons, and structured explanations |
| Support Agent | Assistance, problem-solving, and user-support-oriented queries |
| General Agent | General questions and conversations |

### Agent Workflow

1. User submits a query.
2. The query classifier analyzes the request.
3. The system determines the appropriate agent.
4. Routing confidence is evaluated against the configured threshold.
5. LangGraph orchestrates the selected agent's execution.
6. The agent generates a response using the local LLM.
7. The response is streamed back to the user.
8. Execution details and performance metrics are recorded.
9. The response can be evaluated using DeepEval.

---

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Framework | LangChain |
| Local LLM | Ollama |
| Model | llama3.2:3b |
| Database | MySQL |
| ORM | SQLAlchemy |
| Evaluation | DeepEval |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| API Testing | Pytest |
| Configuration | Python dotenv |
| API Documentation | Swagger / OpenAPI |

---

## Project Structure

```text
ai-agent-eval-platform/
│
├── backend/
│   └── app/
│       ├── agents/
│       │   ├── agent_factory.py
│       │   └── prompts.py
│       │
│       ├── evaluation/
│       │   ├── evaluator.py
│       │   └── test_cases.py
│       │
│       ├── monitoring/
│       │   └── logger.py
│       │
│       ├── orchestration/
│       │   ├── classifier.py
│       │   ├── graph.py
│       │   └── state.py
│       │
│       ├── services/
│       │   └── agent_service.py
│       │
│       ├── config.py
│       ├── database.py
│       ├── main.py
│       ├── models.py
│       └── schemas.py
│
├── dashboard/
│   └── app.py
│
├── tests/
│   ├── test_api.py
│   ├── test_evaluation.py
│   └── test_router.py
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## System Workflow

### 1. Query Classification

The system receives a user query and analyzes it to determine which specialized agent should handle it.

The classifier identifies the query category and produces routing information for the orchestration layer.

### 2. Agent Routing

Based on the classification result, the query is routed to one of the available agents:

- Technical
- Analysis
- Support
- General

A routing confidence threshold is configurable to control routing decisions.

### 3. Agent Orchestration

LangGraph manages the execution workflow using shared state and graph-based orchestration.

The graph coordinates query processing, agent execution, and response handling.

### 4. LLM Generation

The selected agent uses Ollama to invoke the local model:

```text
llama3.2:3b
```

Running the model locally allows experimentation with LLM-powered applications without relying on a cloud model API for generation.

### 5. Streaming

The backend supports streaming responses, allowing generated output to be delivered progressively instead of waiting for the entire response to finish.

### 6. Monitoring and Logging

Execution information is collected to monitor system behavior, including:

- Agent used
- Execution status
- Response latency
- Token usage
- LLM generation performance
- Evaluation results

### 7. Evaluation

DeepEval is used to evaluate AI-generated responses using quality-related metrics.

Evaluation results are stored and can be reviewed to understand the quality and behavior of agent responses.

---

## Monitoring & Evaluation

The platform maintains execution and evaluation data to help analyze AI system performance.

### Monitored Information

- Total agent executions
- Agent execution status
- Response latency
- Token usage
- Agent distribution
- Execution failures
- Evaluation scores

### Evaluation Metrics

| Metric | Purpose |
|---|---|
| Answer Relevance | Measures how relevant the response is to the user query |
| Answer Quality | Evaluates the quality of the generated response |

Evaluation results are persisted to the database for analysis.

---

## Database

The platform uses MySQL for persistent storage and SQLAlchemy as the ORM layer.

### Main Data Entities

| Table | Purpose |
|---|---|
| `agent_runs` | Stores agent execution records |
| `llm_metrics` | Stores LLM performance and token metrics |
| `agent_evaluations` | Stores evaluation results |
| `prompt_versions` | Stores prompt version information |

The database allows the platform to maintain execution history and monitor agent performance over time.

---

## API

The backend is built using FastAPI and exposes REST endpoints for interacting with the system.

### Core Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/chat` | POST | Submit a query to the agent system |
| `/chat/stream` | POST | Stream agent responses |
| `/monitoring/runs` | GET | Retrieve agent execution records |

### API Documentation

Once the backend is running, interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Dashboard

The Streamlit dashboard provides an interface for interacting with the platform and observing its performance.

### Dashboard Capabilities

- Interact with AI agents
- Submit queries
- View generated responses
- Monitor agent executions
- Review performance metrics
- Analyze execution history

---

## Installation & Setup

### Prerequisites

Ensure the following are installed:

- Python 3.10+
- MySQL
- Ollama
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/KarunakarkReddy/ai-agent-eval-platform.git
```

Navigate into the project:

```bash
cd ai-agent-eval-platform
```

---

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/ai_agent_platform

APP_NAME=AI Agent Eval Platform
APP_ENV=development

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

LLM_TEMPERATURE=0.2
ROUTING_CONFIDENCE_THRESHOLD=0.60
```

Update the database credentials according to your local MySQL configuration.

---

### 5. Create the MySQL Database

Open MySQL and execute:

```sql
CREATE DATABASE ai_agent_platform;
```

Ensure your MySQL user has the required permissions to connect to the database.

---

### 6. Install and Run Ollama

Download Ollama:

https://ollama.com/

Pull the required model:

```bash
ollama pull llama3.2:3b
```

Start Ollama:

```bash
ollama serve
```

If Ollama is already running in the background, you do not need to start it again.

---

## Running the Application

Run the application using three terminals.

### Terminal 1 – Ollama

```bash
ollama serve
```

### Terminal 2 – FastAPI Backend

Activate the virtual environment and run:

```bash
uvicorn backend.app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 3 – Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard:

```text
http://localhost:8501
```

---

## Testing

The platform includes tests for API functionality, routing, and evaluation-related logic.

Run the test suite:

```bash
pytest -v
```

### Test Coverage Areas

- API endpoints
- Health endpoint
- Query validation
- Monitoring endpoints
- Routing test cases
- Agent category coverage
- Evaluation-related test logic


## Configuration

The following configuration values can be adjusted through the `.env` file:

| Variable | Description |
|---|---|
| `DATABASE_URL` | MySQL database connection string |
| `APP_NAME` | Application name |
| `APP_ENV` | Application environment |
| `OLLAMA_BASE_URL` | Ollama server URL |
| `OLLAMA_MODEL` | Model used for generation |
| `LLM_TEMPERATURE` | Generation temperature |
| `ROUTING_CONFIDENCE_THRESHOLD` | Minimum routing confidence threshold |

## Future Improvements

Potential improvements to the platform include:

- Advanced agent routing strategies
- Improved evaluation datasets
- Additional DeepEval metrics
- Prompt version comparison
- Agent-level performance comparison
- Better token usage tracking
- Real-time monitoring visualizations
- Evaluation trends over time
- Improved failure analysis
- Docker-based deployment
- CI/CD integration


## Author

**Karunakar Reddy**

AI / Generative AI Engineering Projects

## License

This project is developed for learning, experimentation, and portfolio demonstration purposes.
