
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import Base, engine, get_db
from api import models
from api.agents.planner import PlannerAgent
from api.agents.orchestrator import AgentOrchestrator

from api.agents.execution_service import TaskExecutionService

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Multi-Agent Development Platform",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------- Project schemas ----------

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class PlanRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    request: str = Field(min_length=1, max_length=10000)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str


# ---------- Task schemas ----------

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assigned_agent: str | None = Field(default=None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    dependencies: list[int] = Field(default_factory=list)
    approval_required: bool = False


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    assigned_agent: str | None
    status: str
    priority: int
    dependencies: list[int]
    result: str | None
    error_message: str | None
    approval_status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class TaskStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "ready",
        "running",
        "blocked",
        "awaiting_approval",
        "completed",
        "failed",
        "cancelled",
    ]
    result: str | None = None
    error_message: str | None = None

class ApprovalCreate(BaseModel):
    requested_action: str = Field(min_length=1, max_length=5000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer_comment: str | None = Field(default=None, max_length=5000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: str
    requested_action: str
    reviewer_comment: str | None
    created_at: datetime
    resolved_at: datetime | None
# ---------- Health ----------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "multi-agent-dev-team",
    }


# ---------- Projects ----------

@app.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    project = models.Project(
        name=project_data.name,
        description=project_data.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.post("/projects/plan", status_code=201)
def create_project_plan(
    plan_request: PlanRequest,
    db: Session = Depends(get_db),
):
    planner = PlannerAgent()
    plan = planner.create_plan(
        plan_request.project_name,
        plan_request.request,
    )

    project = models.Project(
        name=plan.project_name,
        description=plan.summary,
    )
    db.add(project)
    db.flush()

    created_tasks = []

    try:
        # First create tasks without dependencies.
        for planned_task in plan.tasks:
            task = models.Task(
                project_id=project.id,
                title=planned_task.title,
                description=planned_task.description,
                assigned_agent=planned_task.assigned_agent,
                priority=planned_task.priority,
                dependencies=[],
                status="pending",
                approval_status="pending",
            )
            db.add(task)
            db.flush()
            created_tasks.append(task)

        # Map planner task numbers (1, 2, 3...) to actual database IDs.
        for index, planned_task in enumerate(plan.tasks):
            dependency_numbers = planned_task.dependencies

            if any(
                number < 1 or number > len(created_tasks)
                for number in dependency_numbers
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Planner returned an invalid dependency number",
                )

            created_tasks[index].dependencies = [
                created_tasks[number - 1].id
                for number in dependency_numbers
            ]

        db.commit()

    except Exception:
        db.rollback()
        raise

    for task in created_tasks:
        db.refresh(task)

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        },
        "plan": plan.model_dump(),
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "assigned_agent": task.assigned_agent,
                "dependencies": task.dependencies,
                "status": task.status,
                "approval_status": task.approval_status,
            }
            for task in created_tasks
        ],
    }


@app.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    statement = select(models.Project).order_by(models.Project.id)
    return list(db.scalars(statement).all())


# ---------- Tasks ----------

@app.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if len(set(task_data.dependencies)) != len(task_data.dependencies):
        raise HTTPException(
            status_code=422,
            detail="Duplicate task dependencies are not allowed",
        )

    if any(dependency_id <= 0 for dependency_id in task_data.dependencies):
        raise HTTPException(
            status_code=422,
            detail="Dependency IDs must be positive integers",
        )

    # A task cannot depend on itself; its ID is assigned after creation.
    if task_data.dependencies:
        dependencies = list(
            db.scalars(
                select(models.Task).where(
                    models.Task.id.in_(task_data.dependencies),
                    models.Task.project_id == project_id,
                )
            ).all()
        )
        found_ids = {task.id for task in dependencies}
        missing_ids = set(task_data.dependencies) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Dependencies must reference existing tasks in the "
                    f"same project. Invalid IDs: {sorted(missing_ids)}"
                ),
            )

    task = models.Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        assigned_agent=task_data.assigned_agent,
        priority=task_data.priority,
        dependencies=task_data.dependencies,
        status="pending",
        approval_status=(
            "pending" if task_data.approval_required else "not_required"
        ),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskResponse],
)
def list_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    if db.get(models.Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    statement = (
        select(models.Task)
        .where(models.Task.project_id == project_id)
        .order_by(models.Task.priority, models.Task.id)
    )
    return list(db.scalars(statement).all())

@app.get("/projects/{project_id}/tasks/ready")
def list_ready_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Return tasks currently eligible for execution."""

    project = db.get(models.Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    statement = (
        select(models.Task)
        .where(models.Task.project_id == project_id)
        .order_by(models.Task.id)
    )

    tasks = list(db.scalars(statement).all())

    orchestrator = AgentOrchestrator()
    ready_tasks = orchestrator.get_ready_tasks(tasks)

    return {
        "project_id": project_id,
        "ready_count": len(ready_tasks),
        "tasks": [
            {
                "task_id": task.task_id,
                "title": task.title,
                "assigned_agent": task.assigned_agent,
                "priority": task.priority,
            }
            for task in ready_tasks
        ],
    }

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/{task_id}/execute", response_model=TaskResponse)
def execute_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """Execute an eligible task using its assigned agent."""

    service = TaskExecutionService()

    try:
        return service.execute_task(db, task_id)
    except ValueError as exc:
        message = str(exc)

        if message == f"Task not found: {task_id}":
            raise HTTPException(status_code=404, detail=message) from exc

        raise HTTPException(status_code=409, detail=message) from exc


@app.patch("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    update: TaskStatusUpdate,
    db: Session = Depends(get_db),
):
    task = db.get(models.Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    # Do not allow execution while approval is pending or rejected.
    if (
        update.status in {"running", "completed"}
        and task.approval_status in {"pending", "rejected"}
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Human approval is pending or rejected. "
                "Obtain approval before running or completing this task."
            ),
        )

    # A task can run only after all its dependencies are completed.
    if update.status in {"running", "completed"} and task.dependencies:
        dependency_tasks = list(
            db.scalars(
                select(models.Task).where(
                    models.Task.id.in_(task.dependencies),
                    models.Task.project_id == task.project_id,
                )
            ).all()
        )

        completed_ids = {
            dependency.id
            for dependency in dependency_tasks
            if dependency.status == "completed"
        }

        missing_or_incomplete = (
            set(task.dependencies) - completed_ids
        )

        if missing_or_incomplete:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Complete all task dependencies before starting. "
                    f"Incomplete dependency IDs: "
                    f"{sorted(missing_or_incomplete)}"
                ),
            )

    now = datetime.now(timezone.utc)

    if update.status == "running" and task.started_at is None:
        task.started_at = now

    if update.status in {"completed", "failed", "cancelled"}:
        task.completed_at = now

    if update.status == "awaiting_approval":
        task.approval_status = "pending"

    task.status = update.status

    if update.result is not None:
        task.result = update.result

    if update.error_message is not None:
        task.error_message = update.error_message

    db.commit()
    db.refresh(task)

    return task


@app.post(
    "/tasks/{task_id}/approvals",
    response_model=ApprovalResponse,
    status_code=201,
)
def request_approval(
    task_id: int,
    approval_data: ApprovalCreate,
    db: Session = Depends(get_db),
):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="Cannot request approval for an already completed task",
        )

    approval = models.ApprovalRequest(
        task_id=task_id,
        requested_action=approval_data.requested_action,
        status="pending",
    )

    task.approval_status = "pending"
    task.status = "awaiting_approval"

    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


@app.get(
    "/approvals/pending",
    response_model=list[ApprovalResponse],
)
def list_pending_approvals(db: Session = Depends(get_db)):
    statement = (
        select(models.ApprovalRequest)
        .where(models.ApprovalRequest.status == "pending")
        .order_by(models.ApprovalRequest.id)
    )
    return list(db.scalars(statement).all())


@app.post(
    "/approvals/{approval_id}/decision",
    response_model=ApprovalResponse,
)
def decide_approval(
    approval_id: int,
    decision_data: ApprovalDecision,
    db: Session = Depends(get_db),
):
    approval = db.get(models.ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    if approval.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This approval request has already been resolved",
        )

    task = db.get(models.Task, approval.task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Associated task not found",
        )

    now = datetime.now(timezone.utc)
    approval.status = decision_data.decision
    approval.reviewer_comment = decision_data.reviewer_comment
    approval.resolved_at = now

    if decision_data.decision == "approved":
        task.approval_status = "approved"
        task.status = "pending"
    else:
        task.approval_status = "rejected"
        task.status = "blocked"

    db.commit()
    db.refresh(approval)
    return approval
