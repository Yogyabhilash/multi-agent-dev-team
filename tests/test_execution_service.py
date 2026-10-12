
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from api.agents.agent_registry import AgentRegistry
from api.agents.base_agent import AgentResult
from api.agents.execution_service import TaskExecutionService


def make_task(**overrides):
    values = {
        "id": 1,
        "project_id": 10,
        "title": "Create login page",
        "description": "Build a basic login page.",
        "assigned_agent": "developer",
        "status": "pending",
        "approval_status": "not_required",
        "dependencies": [],
        "result": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_service(agent):
    registry = AgentRegistry()
    registry.register("developer", agent)
    return TaskExecutionService(registry=registry)


def test_execute_task_saves_successful_result():
    task = make_task()
    db = Mock()
    db.get.return_value = task
    db.execute.return_value.rowcount = 1

    agent = Mock()
    agent.execute.return_value = AgentResult(
        success=True,
        output="Generated login page code",
    )

    service = make_service(agent)
    result = service.execute_task(db, task_id=1)

    assert result.status == "completed"
    assert result.result == "Generated login page code"
    assert result.error_message is None
    assert db.execute.called
    assert db.commit.call_count == 2
    assert isinstance(result.completed_at, datetime)
    assert result.completed_at.tzinfo == timezone.utc
    agent.execute.assert_called_once_with(
        title="Create login page",
        description="Build a basic login page.",
    )


def test_execute_task_rejects_pending_approval():
    task = make_task(approval_status="pending")
    db = Mock()
    db.get.return_value = task

    agent = Mock()
    service = make_service(agent)

    with pytest.raises(ValueError, match="Human approval"):
        service.execute_task(db, task_id=1)

    db.commit.assert_not_called()
    agent.execute.assert_not_called()


def test_execute_task_rejects_non_pending_task():
    task = make_task(status="completed")
    db = Mock()
    db.get.return_value = task

    agent = Mock()
    service = make_service(agent)

    with pytest.raises(ValueError, match="Only pending tasks"):
        service.execute_task(db, task_id=1)

    db.commit.assert_not_called()
    agent.execute.assert_not_called()


def test_execute_task_rejects_incomplete_dependencies():
    task = make_task(dependencies=[2])
    dependency = make_task(
        id=2,
        status="pending",
        assigned_agent=None,
    )

    db = Mock()
    db.get.return_value = task
    db.scalars.return_value.all.return_value = [dependency]

    agent = Mock()
    service = make_service(agent)

    with pytest.raises(ValueError, match="Incomplete dependency IDs"):
        service.execute_task(db, task_id=1)

    db.commit.assert_not_called()
    agent.execute.assert_not_called()


def test_execute_task_records_agent_failure():
    task = make_task()
    db = Mock()
    db.get.return_value = task
    db.execute.return_value.rowcount = 1

    agent = Mock()
    agent.execute.return_value = AgentResult(
        success=False,
        output="",
        error="Model unavailable",
    )

    service = make_service(agent)
    result = service.execute_task(db, task_id=1)

    assert result.status == "failed"
    assert result.error_message == "Model unavailable"
    assert result.completed_at is not None
    assert db.commit.call_count == 2
    agent.execute.assert_called_once()


def test_execute_task_records_unexpected_agent_exception():
    task = make_task()
    db = Mock()
    db.get.return_value = task
    db.execute.return_value.rowcount = 1

    agent = Mock()
    agent.execute.side_effect = RuntimeError("Unexpected failure")

    service = make_service(agent)
    result = service.execute_task(db, task_id=1)

    assert result.status == "failed"
    assert result.error_message == (
        "Agent execution failed: Unexpected failure"
    )
    assert result.completed_at is not None
    assert db.commit.call_count == 2
    agent.execute.assert_called_once()


def test_execute_task_rejects_missing_task():
    db = Mock()
    db.get.return_value = None

    service = TaskExecutionService(registry=AgentRegistry())

    with pytest.raises(ValueError, match="Task not found: 999"):
        service.execute_task(db, task_id=999)

    db.commit.assert_not_called()

def test_execute_task_rejects_failed_claim():
    task = make_task()
    db = Mock()
    db.get.return_value = task

    # Simulate another request having already claimed the task.
    db.execute.return_value.rowcount = 0

    agent = Mock()
    service = make_service(agent)

    with pytest.raises(ValueError, match="Task could not be claimed"):
        service.execute_task(db, task_id=1)

    db.rollback.assert_called_once()
    agent.execute.assert_not_called()