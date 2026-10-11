
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
    """Create an initial structured plan from a software request."""

    def create_plan(self, project_name: str, request: str) -> ProjectPlan:
        if not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        if not request.strip():
            raise ValueError("Project request cannot be empty.")

        tasks = [
            PlannedTask(
                title="Analyze requirements",
                description=f"Identify the main requirements: {request}",
                assigned_agent="planner",
                priority=1,
            ),
            PlannedTask(
                title="Design the architecture",
                description="Define the components and how they interact.",
                assigned_agent="architect",
                priority=2,
                dependencies=[1],
            ),
            PlannedTask(
                title="Implement the backend",
                description="Implement the API and application logic.",
                assigned_agent="backend",
                priority=3,
                dependencies=[2],
            ),
            PlannedTask(
                title="Build the frontend",
                description="Build the user interface and connect it to the API.",
                assigned_agent="frontend",
                priority=3,
                dependencies=[2],
            ),
            PlannedTask(
                title="Test the application",
                description="Test the application and report defects.",
                assigned_agent="qa",
                priority=2,
                dependencies=[3, 4],
            ),
        ]

        return ProjectPlan(
            project_name=project_name.strip(),
            summary=f"Initial implementation plan for: {request.strip()}",
            tasks=tasks,
        )
