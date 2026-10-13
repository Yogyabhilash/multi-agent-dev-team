
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.agents.planner import ProjectPlan


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
    "integrate api and database",
    "integrate backend and database",
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
)


def validate_workflow(plan: ProjectPlan) -> None:
    """Validate implementation, testing, infrastructure, and deployment order."""

    tasks = plan.tasks

    def find_task_numbers(*keywords: str) -> list[int]:
        """Return 1-based task numbers matching any keyword."""
        return [
            number
            for number, task in enumerate(tasks, start=1)
            if any(keyword in task.title.casefold() for keyword in keywords)
        ]

    implementation_tasks = find_task_numbers(*IMPLEMENTATION_KEYWORDS)
    testing_tasks = find_task_numbers(*TESTING_KEYWORDS)
    deployment_tasks = find_task_numbers(*DEPLOYMENT_KEYWORDS)
    infrastructure_tasks = find_task_numbers(*INFRASTRUCTURE_KEYWORDS)

    # Every testing task must depend on preceding implementation tasks.
    for test_number in testing_tasks:
        test_task = tasks[test_number - 1]

        missing_dependencies = [
            implementation_number
            for implementation_number in implementation_tasks
            if implementation_number < test_number
            and implementation_number not in test_task.dependencies
        ]

        if missing_dependencies:
            raise ValueError(
                f"Testing task {test_number} must depend on preceding "
                f"implementation tasks. Missing dependencies: "
                f"{missing_dependencies}"
            )

    # Infrastructure setup must depend on preceding implementation tasks.
    for infrastructure_number in infrastructure_tasks:
        infrastructure_task = tasks[infrastructure_number - 1]

        missing_dependencies = [
            implementation_number
            for implementation_number in implementation_tasks
            if implementation_number < infrastructure_number
            and implementation_number not in infrastructure_task.dependencies
        ]

        if missing_dependencies:
            raise ValueError(
                f"Infrastructure task {infrastructure_number} must depend "
                f"on preceding implementation tasks. Missing dependencies: "
                f"{missing_dependencies}"
            )

        # Infrastructure setup should not be blocked by testing alone.
        # This validator does not require a testing dependency here.

    # Deployment requires a preceding testing task.
    if deployment_tasks and not testing_tasks:
        raise ValueError(
            "Deployment tasks require a testing task before deployment."
        )

    for deployment_number in deployment_tasks:
        deployment_task = tasks[deployment_number - 1]

        has_testing_dependency = any(
            testing_number < deployment_number
            and testing_number in deployment_task.dependencies
            for testing_number in testing_tasks
        )

        if not has_testing_dependency:
            raise ValueError(
                f"Deployment task {deployment_number} must depend "
                "on a preceding testing task."
            )

        # Deployment must depend on preceding implementation tasks.
        missing_implementations = [
            implementation_number
            for implementation_number in implementation_tasks
            if implementation_number < deployment_number
            and implementation_number not in deployment_task.dependencies
        ]

        if missing_implementations:
            raise ValueError(
                f"Deployment task {deployment_number} must depend on "
                f"preceding implementation tasks. Missing dependencies: "
                f"{missing_implementations}"
            )

        # Deployment must depend on preceding infrastructure setup tasks.
        missing_infrastructure = [
            infrastructure_number
            for infrastructure_number in infrastructure_tasks
            if infrastructure_number < deployment_number
            and infrastructure_number not in deployment_task.dependencies
        ]

        if missing_infrastructure:
            raise ValueError(
                f"Deployment task {deployment_number} must depend on "
                f"preceding infrastructure tasks. Missing dependencies: "
                f"{missing_infrastructure}"
            )
