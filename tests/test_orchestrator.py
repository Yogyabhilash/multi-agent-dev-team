
from types import SimpleNamespace

from api.agents.orchestrator import AgentOrchestrator


def make_task(
    task_id,
    title,
    status="pending",
    approval_status="approved",
    priority=3,
    dependencies=None,
    assigned_agent="backend",
):
    """Create a lightweight task for scheduler tests."""
    return SimpleNamespace(
        id=task_id,
        title=title,
        status=status,
        approval_status=approval_status,
        priority=priority,
        dependencies=dependencies or [],
        assigned_agent=assigned_agent,
    )


def test_scheduler_returns_tasks_with_no_dependencies():
    tasks = [
        make_task(1, "Analyze requirements"),
        make_task(2, "Design architecture"),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert [task.task_id for task in ready] == [1, 2]


def test_scheduler_waits_for_dependencies():
    tasks = [
        make_task(1, "Implement backend", status="running"),
        make_task(2, "Test application", dependencies=[1]),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert [task.task_id for task in ready] == []


def test_scheduler_selects_task_after_dependencies_complete():
    tasks = [
        make_task(1, "Implement backend", status="completed"),
        make_task(2, "Test application", dependencies=[1]),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert [task.task_id for task in ready] == [2]


def test_scheduler_excludes_tasks_with_pending_approval():
    tasks = [
        make_task(1, "Implement backend", approval_status="pending"),
        make_task(2, "Build frontend", approval_status="approved"),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert [task.task_id for task in ready] == [2]


def test_scheduler_excludes_rejected_tasks():
    tasks = [
        make_task(1, "Implement backend", approval_status="rejected"),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert ready == []


def test_scheduler_orders_tasks_by_priority_then_id():
    tasks = [
        make_task(3, "Third task", priority=3),
        make_task(2, "Second task", priority=1),
        make_task(1, "First task", priority=1),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert [task.task_id for task in ready] == [1, 2, 3]


def test_scheduler_excludes_tasks_with_missing_dependencies():
    tasks = [
        make_task(2, "Test application", dependencies=[999]),
    ]

    ready = AgentOrchestrator().get_ready_tasks(tasks)

    assert ready == []


def test_scheduler_does_not_modify_original_tasks():
    tasks = [
        make_task(1, "Implement backend"),
    ]

    original_status = tasks[0].status
    original_dependencies = list(tasks[0].dependencies)

    AgentOrchestrator().get_ready_tasks(tasks)

    assert tasks[0].status == original_status
    assert tasks[0].dependencies == original_dependencies
