# Multi-Agent Development Platform

An AI-powered software development platform that coordinates specialized AI agents to plan and execute software development tasks. The goal is to build a collaborative system that can generate, test, debug, and review software while keeping humans involved in important decisions.

The platform uses **FastAPI, PostgreSQL, SQLAlchemy, and Ollama** to provide a foundation for AI-assisted software development with task orchestration, dependency management, and approval-aware execution.

## Features

### Implemented

- **Project management:** Create and retrieve development projects.
- **Task management:** Create, retrieve, list, and update tasks.
- **Task orchestration:** Identify tasks eligible for execution based on status, approval, dependencies, priority, and task ID.
- **Agent registry:** Register and retrieve agents by name.
- **Developer Agent:** Generate code using a locally hosted Ollama language model.
- **Execution service:** Validate tasks, check dependencies, claim tasks for execution, and record execution results.
- **Approval-aware execution:** Prevent execution when approval is pending or rejected.
- **PostgreSQL persistence:** Store project and task information, including execution status, generated output, and errors.
- **Approval requests:** Create approval requests and list, approve, or reject pending requests.
- **REST API:** Expose backend functionality through FastAPI.
- **Automated tests:** Test agent components, orchestration, execution, and API behavior.

### In Progress

- Extracting code reliably from AI model responses.
- Validating generated code before declaring a development task successful.
- Safely testing generated code in an isolated environment.

### Planned

- Specialized frontend, backend, database, testing, and code-review agents.
- AI-driven debugging and automated repair.
- React and TypeScript web dashboard.
- Command-line interface.
- Sandboxed execution of generated code.
- More comprehensive security checks and human approval workflows.
- Optional deployment automation.
- Support for additional local and cloud AI models.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Primary programming language |
| FastAPI | REST API framework |
| Pydantic | Request and response validation |
| SQLAlchemy | Database access and ORM |
| PostgreSQL | Relational database |
| Alembic | Database schema migrations |
| Ollama | Local language model serving |
| Qwen 2.5 3B | Language model used by the Developer Agent |
| Docker Compose | Local PostgreSQL environment |
| Uvicorn | ASGI application server |
| Pytest | Automated testing |
| Git and GitHub | Version control and collaboration |

## Architecture

```text
User / API Client
       |
       v
    FastAPI
       |
       v
Task Orchestrator
       |
       +----------------------+
       |                      |
       v                      v
 Agent Registry         Task Validation
       |
       v
 Developer Agent
       |
       v
    Ollama
  (Qwen 2.5 3B)
       |
       v
 Generated Output
       |
       v
Execution Service
       |
       v
 PostgreSQL
```

The orchestrator identifies eligible tasks and coordinates their execution. The registry resolves the appropriate agent, while the execution service checks task eligibility and dependencies, updates execution status, and persists the result.

**Note:** Generated code is currently returned and stored as output. Reliable code extraction, validation, and isolated execution are ongoing improvements; the platform does not yet provide a complete autonomous software development pipeline.

## Project Structure

```text
multi-agent-dev-team/
├── api/
│   ├── agents/
│   │   ├── agent_registry.py
│   │   ├── base_agent.py
│   │   ├── developer_agent.py
│   │   ├── execution_service.py
│   │   ├── ollama_client.py
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   └── plan_validator.py
│   ├── main.py
│   └── ...
├── migrations/
├── tests/
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Git
- Python compatible with the project dependencies
- Docker Desktop with Docker Compose
- Ollama
- The `qwen2.5:3b` model

### 1. Clone the repository

```powershell
git clone https://github.com/Yogyabhilash/multi-agent-dev-team.git
cd multi-agent-dev-team
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file with the database connection settings expected by the application. Use the credentials configured in your local PostgreSQL environment.

Never commit `.env` files, passwords, API keys, or other secrets to GitHub.

### 4. Start PostgreSQL

```powershell
docker compose up -d
```

Ensure the database settings in your environment match the PostgreSQL configuration.

### 5. Run database migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 6. Start Ollama

Install Ollama if necessary, then download the model:

```powershell
ollama pull qwen2.5:3b
```

Ensure the Ollama service is running and accessible at `http://localhost:11434`.

### 7. Start the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

### 8. Explore the API

With the server running, open:

- **Interactive API documentation:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health

### 9. Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The current verified test suite contains **63 passing tests**. Run the suite again after making changes to confirm the current result.

## Important API Endpoint

### Execute a task

```http
POST /tasks/{task_id}/execute
```

This endpoint attempts to execute a task through the configured agent. The service checks task eligibility, approval status, and dependencies, then records the execution status and result.

A task must satisfy the service's execution requirements before it can run. Generated model output should not be treated as safe or correct code without further validation.

See the interactive API documentation at `/docs` for the available request and response schemas.

## Development Roadmap

1. **Improve code generation:** Extract source code from model responses and validate syntax.
2. **Improve execution reliability:** Add automated checks and safer, isolated execution.
3. **Expand agent capabilities:** Introduce specialized testing, debugging, review, and frontend/backend agents.
4. **Improve workflow management:** Strengthen approvals, dependency handling, retries, and error reporting.
5. **Build the frontend:** Develop a React and TypeScript dashboard for projects, tasks, and agent activity.
6. **Prepare for deployment:** Add security hardening, monitoring, and optional deployment automation.

## Security Considerations

- Store secrets and database credentials in environment variables.
- Do not commit `.env` files or credentials.
- Treat AI-generated content as untrusted input.
- Validate generated code before considering it successful.
- Do not execute arbitrary generated code directly on the host machine.
- Use an isolated environment with appropriate resource and permission limits for code execution.
- Require explicit authorization for sensitive operations and production deployments.

## Development Status

This project is under active development. The current implementation provides a backend API, persistent task management, approval-aware task execution, agent registration, task orchestration, and a locally hosted AI-powered Developer Agent.

The longer-term objective is to evolve this foundation into a reliable multi-agent development platform capable of coordinating software creation, testing, debugging, and review with appropriate human oversight.

## Contributing

Contributions, bug reports, and suggestions are welcome. Please test changes locally and run the automated test suite before submitting them.

## License

No license has been specified yet. Add a `LICENSE` file before explicitly granting others permission to reuse, modify, or distribute the project.
