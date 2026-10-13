
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

    MAX_ATTEMPTS = 3

    ALLOWED_AGENTS = {
        "planner",
        "architect",
        "backend",
        "frontend",
        "qa",
        "devops",
    }

    IMPLEMENTATION_KEYWORDS = (
        "implement backend",
        "develop backend",
        "build backend",
        "implement frontend",
        "develop frontend",
        "build frontend",
        "implement authentication",
        "implement product",
        "implement crud",
        "implement database",
        "develop database",
        "implement api",
        "implement postgres",
        "develop api",
        "develop service",
        "build api",
        "build service",
        "integrate authentication",
        "authentication integration",
        "integrate login",
        "integrate frontend and backend",
    )

    TESTING_KEYWORDS = (
        "test",
        "quality assurance",
        "qa testing",
    )

    DEPLOYMENT_KEYWORDS = (
        "deploy",
        "deployment",
        "publish to production",
    )

    INFRASTRUCTURE_KEYWORDS = (
        "setup infrastructure",
        "setup deployment infrastructure",
        "set up infrastructure",
        "configure infrastructure",
        "provision infrastructure",
        "prepare staging infrastructure",
        "deployment infrastructure",
        "infrastructure setup",
        "setup staging environment",
        "set up staging environment",
        "prepare staging environment",
        "configure staging environment",
        "integrate api and database",
        "integrate backend and database",
        "integrate frontend and backend",
        "integrate authentication",
        "authentication integration",
    )

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
  "project_name": {json.dumps(project_name)},
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
- Every dependency must refer to an earlier task.
- The first task must have no dependencies.
- Include architecture, implementation, and testing tasks as appropriate.
- Use clear implementation task titles, such as "Implement backend",
  "Implement frontend", and "Implement authentication".
- Every testing task must depend on all preceding implementation tasks,
  including authentication integration.
- Every deployment task must depend on preceding implementation tasks,
  infrastructure setup, and a preceding testing task.
- Do not include tasks unrelated to the user's request.
- Do not invent dependencies on tasks that appear later in the plan.
- Assign database and backend API implementation to backend.
- Assign frontend implementation to frontend.
- Assign API and database architecture/design to architect.
- Assign automated testing to qa.
- Assign deployment and infrastructure setup to devops.
- Authentication integration must depend on preceding frontend and backend tasks.
"""

        correction_prompt = prompt
        last_error: Exception | None = None

        for attempt in range(self.MAX_ATTEMPTS):
            raw_response = self.ollama_client.generate(correction_prompt)

            try:
                data = json.loads(raw_response)

                # Normalize valid integer priorities into the supported range.
                if isinstance(data, dict) and isinstance(data.get("tasks"), list):
                    for task in data["tasks"]:
                        if not isinstance(task, dict):
                            continue

                        priority = task.get("priority")

                        # Do not silently convert strings, floats, or booleans.
                        if type(priority) is int:
                            task["priority"] = max(1, min(5, priority))

                self._normalize_dependency_references(data)
                plan = ProjectPlan.model_validate(data)

                # Repair workflow dependencies before strict validation.
                self._repair_workflow_dependencies(plan)
                self._validate_plan(plan, project_name)

                return plan

            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = ValueError(
                    "Ollama returned an invalid project plan. "
                    "Please try again."
                )
                last_error.__cause__ = exc

            except ValueError as exc:
                last_error = exc

            if attempt < self.MAX_ATTEMPTS - 1:
                correction_prompt = f"""
{prompt}

Your previous response failed validation.

Validation error:
{last_error}

Previous response:
{raw_response}

Generate a corrected, complete project plan as a single JSON object.

Carefully correct the specific validation error.

Dependency requirements:
- Dependencies are 1-based task numbers.
- The plan MUST contain between 4 and 12 tasks.
- Count the tasks before returning the JSON.
- Do not return fewer than 4 tasks or more than 12 tasks.
- Return a complete plan, not a partial plan.
- Dependencies must refer only to earlier tasks.
- The first task must have no dependencies.
- Every testing task must depend on all preceding implementation tasks,
  including authentication integration.
- Infrastructure setup must depend on preceding implementation tasks.
- Every deployment task must depend on preceding implementation tasks,
  preceding infrastructure setup, and a preceding testing task.
- Keep all tasks relevant to the requested project.
- Return only valid JSON, without Markdown fences.
"""

        raise ValueError(
            f"Unable to generate a valid project plan after "
            f"{self.MAX_ATTEMPTS} attempts. "
            f"Last validation error: {last_error}"
        ) from last_error

    @staticmethod
    def _repair_workflow_dependencies(plan: ProjectPlan) -> None:
        """Repair dependencies required by the project workflow."""
        tasks = plan.tasks

        def matches(title: str, keywords: tuple[str, ...]) -> bool:
            title = title.casefold()
            return any(keyword in title for keyword in keywords)

        implementation_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(task.title, PlannerAgent.IMPLEMENTATION_KEYWORDS)
        ]

        testing_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(task.title, PlannerAgent.TESTING_KEYWORDS)
        ]

        deployment_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(task.title, PlannerAgent.DEPLOYMENT_KEYWORDS)
        ]

        infrastructure_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(task.title, PlannerAgent.INFRASTRUCTURE_KEYWORDS)
        ]

        frontend_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(
                task.title,
                (
                    "implement frontend",
                    "develop frontend",
                    "build frontend",
                ),
            )
        ]

        backend_numbers = [
            number
            for number, task in enumerate(tasks, start=1)
            if matches(
                task.title,
                (
                    "implement backend",
                    "develop backend",
                    "build backend",
                    "implement api",
                    "develop api",
                    "build api",
                    "implement database",
                    "develop database",
                    "implement crud",
                    "implement authentication",
                ),
            )
        ]

        integration_keywords = (
            "implement authentication",
            "integrate authentication",
            "authentication integration",
            "integrate login",
            "integrate frontend and backend",
        )

        # Authentication integration depends on preceding frontend/backend tasks.
        for number, task in enumerate(tasks, start=1):
            if matches(task.title, integration_keywords):
                required_dependencies = set(
                    frontend_numbers + backend_numbers
                )

                for dependency in sorted(required_dependencies):
                    if (
                        dependency < number
                        and dependency not in task.dependencies
                    ):
                        task.dependencies.append(dependency)

        # Testing depends on every preceding implementation task.
        for test_number in testing_numbers:
            test_task = tasks[test_number - 1]

            for implementation_number in implementation_numbers:
                if (
                    implementation_number < test_number
                    and implementation_number not in test_task.dependencies
                ):
                    test_task.dependencies.append(implementation_number)

        # Infrastructure setup depends on preceding implementation tasks.
        # It does not need to wait for application tests to finish.
        for infrastructure_number in infrastructure_numbers:
            infrastructure_task = tasks[infrastructure_number - 1]
            # Remove testing dependencies from infrastructure setup.
            infrastructure_task.dependencies = [
                dependency
                for dependency in infrastructure_task.dependencies
                if dependency not in testing_numbers
            ]
            
            # Remove unnecessary testing dependencies from infrastructure setup.
            infrastructure_task.dependencies = [
                dependency
                for dependency in infrastructure_task.dependencies
                if dependency not in testing_numbers
            ]

            for implementation_number in implementation_numbers:
                if (
                    implementation_number < infrastructure_number
                    and implementation_number
                    not in infrastructure_task.dependencies
                ):
                    infrastructure_task.dependencies.append(
                        implementation_number
                    )

        # Deployment depends on preceding implementation tasks,
        # infrastructure setup, and the latest preceding testing task.
        for deployment_number in deployment_numbers:
            deployment_task = tasks[deployment_number - 1]

            required_dependencies = [
                number
                for number in implementation_numbers
                if number < deployment_number
            ]

            required_dependencies.extend(
                number
                for number in infrastructure_numbers
                if number < deployment_number
            )

            preceding_tests = [
                number
                for number in testing_numbers
                if number < deployment_number
            ]

            if preceding_tests:
                required_dependencies.append(preceding_tests[-1])

            for dependency in sorted(set(required_dependencies)):
                if dependency not in deployment_task.dependencies:
                    deployment_task.dependencies.append(dependency)

    def _validate_plan(
        self,
        plan: ProjectPlan,
        requested_project_name: str,
    ) -> None:
        """Validate project details, tasks, dependencies, and workflow."""

        if plan.project_name.strip() != requested_project_name:
            raise ValueError(
                "Ollama returned a project name that does not match "
                "the requested project."
            )

        if not 4 <= len(plan.tasks) <= 12:
            raise ValueError(
                "The generated plan must contain between 4 and 12 tasks."
            )

        for task_number, task in enumerate(plan.tasks, start=1):
            if task.assigned_agent not in self.ALLOWED_AGENTS:
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

        validate_workflow(plan)

    @staticmethod
    def _normalize_dependency_references(data: dict) -> None:
        """Convert dependency task titles into earlier 1-based task numbers."""
        tasks = data.get("tasks")

        if not isinstance(tasks, list):
            return

        for task_number, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                continue

            dependencies = task.get("dependencies")

            if not isinstance(dependencies, list):
                continue

            normalized = []

            for dependency in dependencies:
                if type(dependency) is int:
                    normalized.append(dependency)
                    continue

                if isinstance(dependency, str):
                    # Resolve only titles belonging to earlier tasks.
                    matching_numbers = [
                        number
                        for number, previous_task in enumerate(
                            tasks[: task_number - 1], start=1
                        )
                        if isinstance(previous_task, dict)
                        and isinstance(previous_task.get("title"), str)
                        and previous_task["title"].strip().casefold()
                        == dependency.strip().casefold()
                    ]

                    if len(matching_numbers) == 1:
                        normalized.append(matching_numbers[0])
                        continue

                # Leave unrecognized references untouched so Pydantic
                # rejects them instead of silently guessing.
                normalized.append(dependency)

            task["dependencies"] = normalized
