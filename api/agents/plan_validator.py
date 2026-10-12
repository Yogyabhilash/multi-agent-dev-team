
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.agents.planner import ProjectPlan


def validate_workflow(plan: ProjectPlan) -> None:
    """Validate implementation, testing, and deployment order."""

    tasks = plan.tasks

    def find_task_numbers(*keywords: str) -> list[int]:
        """Return 1-based task numbers matching any keyword."""
        return [
            number
            for number, task in enumerate(tasks, start=1)
            if any(keyword in task.title.lower() for keyword in keywords)
        ]

    implementation_tasks = find_task_numbers(
        "implement backend",
        "develop backend",
        "build backend",
        "implement frontend",
        "develop frontend",
        "build frontend",
        "implement authentication",
        "implement product",
    )

    testing_tasks = find_task_numbers(
        "test",
        "quality assurance",
        "qa testing",
    )

    deployment_tasks = find_task_numbers(
        "deploy",
        "deployment",
        "publish to production",
    )

    # Testing must depend on preceding implementation tasks.
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

    # Deployment requires an earlier testing task.
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
