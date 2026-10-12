import pytest
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


from unittest.mock import Mock
from types import SimpleNamespace

from api.agents.agent_registry import AgentRegistry
from api.agents.base_agent import AgentResult
from api.agents.orchestrator import AgentOrchestrator


def make_execution_task(**overrides):
    task = {
        "id": 1,
        "title": "Create login page",
        "description": "Build a basic login page.",
        "assigned_agent": "developer",
        "status": "pending",
        "approval_status": "not_required",
        "dependencies": [],
        "priority": 2,
    }
    task.update(overrides)
    return SimpleNamespace(**task)


def test_execute_task_dispatches_to_registered_agent():
    agent = Mock()
    agent.execute.return_value = AgentResult(
        success=True,
        output="Generated login page code",
    )

    registry = AgentRegistry()
    registry.register("developer", agent)
    orchestrator = AgentOrchestrator(registry=registry)

    task = make_execution_task()
    result = orchestrator.execute_task(task)

    assert result.success is True
    assert result.output == "Generated login page code"
    agent.execute.assert_called_once_with(
        title="Create login page",
        description="Build a basic login page.",
    )


def test_execute_task_rejects_non_pending_task():
    agent = Mock()
    registry = AgentRegistry()
    registry.register("developer", agent)
    orchestrator = AgentOrchestrator(registry=registry)

    result = orchestrator.execute_task(
        make_execution_task(status="completed")
    )

    assert result.success is False
    assert result.error == "Only pending tasks can be executed."
    agent.execute.assert_not_called()


def test_execute_task_rejects_pending_approval():
    agent = Mock()
    registry = AgentRegistry()
    registry.register("developer", agent)
    orchestrator = AgentOrchestrator(registry=registry)

    result = orchestrator.execute_task(
        make_execution_task(approval_status="pending")
    )

    assert result.success is False
    assert result.error == "Human approval is pending or rejected."
    agent.execute.assert_not_called()


def test_execute_task_rejects_unassigned_agent():
    orchestrator = AgentOrchestrator(registry=AgentRegistry())

    result = orchestrator.execute_task(
        make_execution_task(assigned_agent=None)
    )

    assert result.success is False
    assert result.error == "No agent is assigned to this task."


def test_execute_task_rejects_unknown_agent():
    orchestrator = AgentOrchestrator(registry=AgentRegistry())

    result = orchestrator.execute_task(
        make_execution_task(assigned_agent="tester")
    )

    assert result.success is False
    assert result.error == "No agent registered for: tester"


def test_execute_task_refuses_unverified_dependencies():
    agent = Mock()
    registry = AgentRegistry()
    registry.register("developer", agent)
    orchestrator = AgentOrchestrator(registry=registry)

    task = make_execution_task(dependencies=[99])

    with pytest.raises(ValueError, match="Dependency completion"):
        orchestrator.execute_task(task)

    agent.execute.assert_not_called()
