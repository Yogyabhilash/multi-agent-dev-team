
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "multi-agent-dev-team",
    }


@patch("api.main.TaskExecutionService")
def test_execute_task_returns_updated_task(mock_service_class):
    task = {
        "id": 1,
        "project_id": 10,
        "title": "Create login page",
        "description": "Build a basic login page.",
        "assigned_agent": "developer",
        "status": "completed",
        "priority": 2,
        "dependencies": [],
        "result": "Generated login page code",
        "error_message": None,
        "approval_status": "not_required",
        "started_at": "2026-10-13T00:00:00Z",
        "completed_at": "2026-10-13T00:00:05Z",
        "created_at": "2026-10-12T00:00:00Z",
    }

    mock_service_class.return_value.execute_task.return_value = task

    response = client.post("/tasks/1/execute")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["result"] == "Generated login page code"
    mock_service_class.return_value.execute_task.assert_called_once()


@patch("api.main.TaskExecutionService")
def test_execute_task_returns_404_for_missing_task(mock_service_class):
    mock_service_class.return_value.execute_task.side_effect = ValueError(
        "Task not found: 999"
    )

    response = client.post("/tasks/999/execute")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found: 999"


@patch("api.main.TaskExecutionService")
def test_execute_task_returns_409_when_execution_is_blocked(
    mock_service_class,
):
    mock_service_class.return_value.execute_task.side_effect = ValueError(
        "Human approval is pending or rejected."
    )

    response = client.post("/tasks/1/execute")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Human approval is pending or rejected."
    )
