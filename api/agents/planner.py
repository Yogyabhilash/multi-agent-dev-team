
from pydantic import BaseModel, Field


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
    """Create a structured plan based on a software request."""

    def create_plan(self, project_name: str, request: str) -> ProjectPlan:
        if not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        if not request.strip():
            raise ValueError("Project request cannot be empty.")

        request_lower = request.lower()

        # Step 1: Analyze requirements and design the architecture.
        tasks = [
            PlannedTask(
                title="Analyze requirements",
                description=(
                    f"Identify the main requirements: {request.strip()}"
                ),
                assigned_agent="planner",
                priority=1,
            ),
            PlannedTask(
                title="Design the architecture",
                description=(
                    "Define the components, data flow, and how they interact."
                ),
                assigned_agent="architect",
                priority=2,
                dependencies=[1],
            ),
        ]

        # Step 2: Add authentication if requested.
        if any(
            word in request_lower
            for word in [
                "login",
                "authentication",
                "sign in",
                "signup",
                "register",
            ]
        ):
            tasks.append(
                PlannedTask(
                    title="Implement authentication",
                    description=(
                        "Build login, registration, and secure "
                        "authentication as required."
                    ),
                    assigned_agent="backend",
                    priority=2,
                    dependencies=[2],
                )
            )

        # Step 3: Add e-commerce features if requested.
        if any(
            word in request_lower
            for word in [
                "e-commerce",
                "ecommerce",
                "shop",
                "store",
                "payment",
                "cart",
            ]
        ):
            tasks.append(
                PlannedTask(
                    title="Implement product and order features",
                    description=(
                        "Build the relevant product catalog, cart, "
                        "and order workflows."
                    ),
                    assigned_agent="backend",
                    priority=3,
                    dependencies=[2],
                )
            )

        # Step 4: Add the core backend and frontend tasks.
        tasks.extend(
            [
                PlannedTask(
                    title="Implement the backend",
                    description=(
                        "Implement API endpoints, data handling, "
                        "and application logic."
                    ),
                    assigned_agent="backend",
                    priority=3,
                    dependencies=[2],
                ),
                PlannedTask(
                    title="Build the frontend",
                    description=(
                        "Build a responsive user interface "
                        "and connect it to the API."
                    ),
                    assigned_agent="frontend",
                    priority=3,
                    dependencies=[2],
                ),
            ]
        )

        # Find task numbers so testing depends on both implementations.
        backend_number = next(
            index
            for index, task in enumerate(tasks, start=1)
            if task.title == "Implement the backend"
        )

        frontend_number = next(
            index
            for index, task in enumerate(tasks, start=1)
            if task.title == "Build the frontend"
        )

        # Step 5: Test after the backend and frontend tasks.
        tasks.append(
            PlannedTask(
                title="Test the application",
                description=(
                    "Test functionality, API behavior, "
                    "and responsive design."
                ),
                assigned_agent="qa",
                priority=2,
                dependencies=[backend_number, frontend_number],
            )
        )

        return ProjectPlan(
            project_name=project_name.strip(),
            summary=(
                f"Initial implementation plan for: {request.strip()}"
            ),
            tasks=tasks,
        )
