
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api import models
from api.agents.agent_registry import AgentRegistry
from api.agents.base_agent import AgentResult


class TaskExecutionService:
    """Execute tasks and persist their status and results."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or AgentRegistry.with_default_agents()

    def execute_task(self, db: Session, task_id: int) -> models.Task:
        """Execute an eligible task and save its final state."""

        task = db.get(models.Task, task_id)

        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if task.status != "pending":
            raise ValueError("Only pending tasks can be executed.")

        if task.approval_status in {"pending", "rejected"}:
            raise ValueError("Human approval is pending or rejected.")

        if not task.assigned_agent:
            raise ValueError("No agent is assigned to this task.")

        if task.dependencies:
            dependencies = list(
                db.scalars(
                    select(models.Task).where(
                        models.Task.id.in_(task.dependencies),
                        models.Task.project_id == task.project_id,
                    )
                ).all()
            )

            completed_ids = {
                dependency.id
                for dependency in dependencies
                if dependency.status == "completed"
            }

            incomplete_ids = set(task.dependencies) - completed_ids

            if incomplete_ids:
                raise ValueError(
                    "Complete all task dependencies before execution. "
                    f"Incomplete dependency IDs: {sorted(incomplete_ids)}"
                )

        try:
            agent = self.registry.get(task.assigned_agent)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

        claim_time = datetime.now(timezone.utc)

        claim_result = db.execute(
            update(models.Task)
            .where(
                models.Task.id == task_id,
                models.Task.status == "pending",
                models.Task.approval_status.notin_(["pending", "rejected"]),
            )
            .values(
                status="running",
                started_at=claim_time,
                error_message=None,
            )
        )

        if claim_result.rowcount != 1:
            db.rollback()
            raise ValueError(
                "Task could not be claimed. It may already be running "
                "or its approval status may have changed."
            )

        db.commit()
        db.refresh(task)

        try:
            result: AgentResult = agent.execute(
                title=task.title,
                description=task.description or "",
            )

            if result.success:
                task.status = "completed"
                task.result = result.output
                task.error_message = None
            else:
                task.status = "failed"
                task.result = result.output
                task.error_message = result.error or "Agent execution failed."

        except Exception as exc:
            task.status = "failed"
            task.error_message = f"Agent execution failed: {exc}"

        task.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(task)

        return task
