
from dataclasses import dataclass

from api.models import Task


@dataclass(frozen=True)
class ScheduledTask:
    """A task selected for potential execution."""

    task_id: int
    title: str
    assigned_agent: str | None
    priority: int


class AgentOrchestrator:
    """Select tasks that are eligible to execute."""

    def get_ready_tasks(self, tasks: list[Task]) -> list[ScheduledTask]:
        """Return eligible tasks in priority order without modifying them."""

        tasks_by_id = {task.id: task for task in tasks}
        ready_tasks: list[ScheduledTask] = []

        for task in tasks:
            if task.status != "pending":
                continue

            if task.approval_status in {"pending", "rejected"}:
                continue

            dependencies_completed = all(
                dependency_id in tasks_by_id
                and tasks_by_id[dependency_id].status == "completed"
                for dependency_id in task.dependencies
            )

            if not dependencies_completed:
                continue

            ready_tasks.append(
                ScheduledTask(
                    task_id=task.id,
                    title=task.title,
                    assigned_agent=task.assigned_agent,
                    priority=task.priority,
                )
            )

        return sorted(
            ready_tasks,
            key=lambda task: (task.priority, task.task_id),
        )
