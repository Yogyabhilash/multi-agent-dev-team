# Multi-Agent Development Platform

An AI-powered software development platform designed to plan, build, test, debug, and review software using specialized AI agents, with human approval at important stages.

## Project Goals

- Convert user requirements into manageable development tasks.
- Coordinate specialized AI agents.
- Generate frontend and backend code.
- Design and manage database schemas.
- Run automated tests and attempt to repair detected errors.
- Review changes and request human approval for important actions.
- Provide a foundation for local and cloud AI models.

## Current Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| FastAPI | Backend API framework |
| SQLAlchemy | Database interaction and ORM |
| PostgreSQL | Relational database |
| Alembic | Database schema migrations |
| Docker Compose | Local database environment |
| Git and GitHub | Version control and source-code hosting |
| Uvicorn | Runs the FastAPI application |

## Current Features

- Health-check endpoint.
- Create and list projects.
- Create and list project tasks.
- Retrieve individual tasks and update their status.
- Create approval requests.
- List pending approvals.
- Approve or reject approval requests.
- Store project and task data in PostgreSQL.

## Planned Features

- AI planning and architecture agent.
- Specialized frontend, backend, and database agents.
- AI-powered code generation.
- Automated testing and debugging.
- Code review and security checks.
- Human approval workflow integration.
- React and TypeScript web dashboard.
- Command-line interface.
- Sandboxed code execution.
- Local and cloud AI model support.
- Optional deployment automation.

## Project Structure

```text
multi-agent-dev-team/
├── api/                    # FastAPI backend and database models
├── cli/                    # Planned command-line interface
├── migrations/              # Alembic database migrations
├── tests/                   # Automated tests
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python
- Docker Desktop with Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Yogyabhilash/multi-agent-dev-team.git
cd multi-agent-dev-team
```

### 2. Install dependencies

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure the database

Create a local `.env` file containing the PostgreSQL connection string required by the application. Use the database credentials configured in your local Docker environment. Do not commit `.env` or real credentials to GitHub.

### 4. Start PostgreSQL

```powershell
docker compose up -d
```

### 5. Run database migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 6. Start the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

### 7. Open the API documentation

Visit:

- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Development Status

This project is under active development. The current version provides the initial backend API, PostgreSQL persistence, task management, and approval-request functionality. AI agent orchestration and complete website generation are planned development goals, not yet completed features.

## Security

- Keep API keys and database credentials in environment variables.
- Never commit `.env` files or secrets.
- Run generated code in an isolated environment before execution.
- Require human approval for sensitive actions and production deployments.