
from dataclasses import dataclass

from api.models import Task
from api.agents.agent_registry import AgentRegistry
from api.agents.base_agent import AgentResult


@dataclass(frozen=True)
class ScheduledTask:
    """A task selected for potential execution."""

    task_id: int
    title: str
    assigned_agent: str | None
    priority: int


class AgentOrchestrator:
    """Select eligible tasks and dispatch them to registered agents."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or AgentRegistry.with_default_agents()

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

    def execute_task(self, task: Task) -> AgentResult:
        """Dispatch a task to its registered agent.

        This method generates a result but does not change database state.
        """

        if task.status != "pending":
            return AgentResult(
                success=False,
                output="",
                error="Only pending tasks can be executed.",
            )

        if task.approval_status in {"pending", "rejected"}:
            return AgentResult(
                success=False,
                output="",
                error="Human approval is pending or rejected.",
            )

        if task.dependencies:
            raise ValueError(
                "Dependency completion must be verified against the database "
                "before executing this task."
            )

        if not task.assigned_agent:
            return AgentResult(
                success=False,
                output="",
                error="No agent is assigned to this task.",
            )

        try:
            agent = self.registry.get(task.assigned_agent)
        except ValueError as exc:
            return AgentResult(
                success=False,
                output="",
                error=str(exc),
            )

        return agent.execute(
            title=task.title,
            description=task.description or "",
        )
