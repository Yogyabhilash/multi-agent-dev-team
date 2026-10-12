import json

from pydantic import BaseModel, Field, ValidationError

from api.agents.ollama_client import OllamaClient
from api.agents.plan_validator import validate_workflow


class PlannedTask(BaseModel):
    """One task produced by the planner."""

    title: str = Field(min_length=1, max_length=200)
    description: str
    assigned_agent: str
    priority: int = Field(default=3, ge=1, le=5)
    dependencies: list[int] = Field(default_factory=list)


class ProjectPlan(BaseModel):
    """A structured plan for a software project."""

    project_name: str = Field(min_length=1, max_length=200)
    summary: str
    tasks: list[PlannedTask] = Field(min_length=1)


class PlannerAgent:
    """Generate and validate project plans using a local Ollama model."""

    def __init__(self, ollama_client: OllamaClient | None = None):
        self.ollama_client = ollama_client or OllamaClient()

    def create_plan(self, project_name: str, request: str) -> ProjectPlan:
        project_name = project_name.strip()
        request = request.strip()

        if not project_name:
            raise ValueError("Project name cannot be empty.")

        if not request:
            raise ValueError("Project request cannot be empty.")

        prompt = f"""
You are a software project planning agent.

Create a practical implementation plan for the user's software project.

Project name: {project_name}
User request: {request}

Return ONLY a valid JSON object. Do not use Markdown fences.

Use exactly this structure:
{{
  "project_name": "{project_name}",
  "summary": "A short summary of the project",
  "tasks": [
    {{
      "title": "Analyze requirements",
      "description": "Identify the requirements",
      "assigned_agent": "planner",
      "priority": 1,
      "dependencies": []
    }}
  ]
}}

Rules:
- Include between 4 and 12 tasks.
- Use only these assigned_agent values:
  planner, architect, backend, frontend, qa, devops.
- Priority must be an integer from 1 to 5.
- Dependencies are 1-based task numbers.
- A dependency must refer to an earlier task.
- The first task must have no dependencies.
- Include architecture, implementation, and testing tasks as appropriate.
- Do not include tasks unrelated to the user's request.
"""

        raw_response = self.ollama_client.generate(prompt)

        try:
            data = json.loads(raw_response)
            plan = ProjectPlan.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(
                "Ollama returned an invalid project plan. "
                "Please try again."
            ) from exc

        if plan.project_name.strip() != project_name:
            raise ValueError(
                "Ollama returned a project name that does not match "
                "the requested project."
            )

        if not 4 <= len(plan.tasks) <= 12:
            raise ValueError(
                "The generated plan must contain between 4 and 12 tasks."
            )

        allowed_agents = {
            "planner",
            "architect",
            "backend",
            "frontend",
            "qa",
            "devops",
        }

        for task_number, task in enumerate(plan.tasks, start=1):
            if task.assigned_agent not in allowed_agents:
                raise ValueError(
                    f"Task {task_number} has an unsupported assigned agent."
                )

            if len(set(task.dependencies)) != len(task.dependencies):
                raise ValueError(
                    f"Task {task_number} contains duplicate dependencies."
                )

            for dependency in task.dependencies:
                if dependency < 1 or dependency >= task_number:
                    raise ValueError(
                        f"Task {task_number} has an invalid dependency: "
                        f"{dependency}. Dependencies must refer to "
                        "earlier tasks."
                    )

        if plan.tasks[0].dependencies:
            raise ValueError("The first task must not have dependencies.")

        # Validate only after every task has passed individual checks.
        # Returning inside the loop skips later tasks and fails when no
        # task has dependencies.
        validate_workflow(plan)
        return plan
