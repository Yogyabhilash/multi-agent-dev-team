
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_create_and_list_projects():
    response = client.post(
        "/projects",
        json={
            "name": "Automated Test Project",
            "description": "Created by an API test",
        },
    )

    assert response.status_code == 201
    project = response.json()
    assert project["name"] == "Automated Test Project"
    assert project["id"] > 0

    list_response = client.get("/projects")

    assert list_response.status_code == 200
    assert any(
        item["id"] == project["id"]
        for item in list_response.json()
    )


def test_create_task_for_existing_project():
    project_response = client.post(
        "/projects",
        json={
            "name": "Task API Test Project",
            "description": "Project for testing tasks",
        },
    )

    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Test Planner Task",
            "description": "Check task creation",
            "assigned_agent": "planner",
            "priority": 2,
            "dependencies": [],
            "approval_required": False,
        },
    )

    assert task_response.status_code == 201
    task = task_response.json()

    assert task["project_id"] == project_id
    assert task["title"] == "Test Planner Task"
    assert task["assigned_agent"] == "planner"
    assert task["status"] == "pending"


def test_create_task_for_missing_project():
    response = client.post(
        "/projects/999999999/tasks",
        json={
            "title": "Task for a missing project",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

def test_task_cannot_run_without_approval():
    project_response = client.post(
        "/projects",
        json={"name": "Approval Test Project"},
    )
    project_id = project_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Task requiring approval",
            "approval_required": True,
        },
    )
    task_id = task_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "running"},
    )

    assert response.status_code == 409
    assert "Human approval is pending or rejected" in response.json()["detail"]


def test_task_cannot_run_before_dependencies_complete():
    project_response = client.post(
        "/projects",
        json={"name": "Dependency Test Project"},
    )
    project_id = project_response.json()["id"]

    dependency_response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "First task"},
    )
    dependency_id = dependency_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Dependent task",
            "dependencies": [dependency_id],
        },
    )
    task_id = task_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "running"},
    )

    assert response.status_code == 409
    assert "Complete all task dependencies before starting" in response.json()["detail"]
    assert str(dependency_id) in response.json()["detail"]


def test_list_ready_tasks_returns_eligible_tasks():
    project_response = client.post(
        "/projects",
        json={"name": "Ready Tasks Test Project"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Ready task",
            "assigned_agent": "developer",
            "priority": 2,
            "dependencies": [],
            "approval_required": False,
        },
    )
    assert task_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks/ready"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == project_id
    assert data["ready_count"] == 1
    assert data["tasks"][0]["title"] == "Ready task"
    assert data["tasks"][0]["assigned_agent"] == "developer"
    assert data["tasks"][0]["priority"] == 2


def test_list_ready_tasks_excludes_tasks_awaiting_approval():
    project_response = client.post(
        "/projects",
        json={"name": "Pending Approval Test Project"},
    )
    project_id = project_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Task awaiting approval",
            "approval_required": True,
        },
    )
    assert task_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks/ready"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["ready_count"] == 0
    assert data["tasks"] == []


def test_list_ready_tasks_excludes_tasks_with_incomplete_dependencies():
    project_response = client.post(
        "/projects",
        json={"name": "Incomplete Dependencies Test Project"},
    )
    project_id = project_response.json()["id"]

    dependency_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "First task",
            "approval_required": False,
        },
    )
    assert dependency_response.status_code == 201
    dependency_id = dependency_response.json()["id"]

    dependent_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Dependent task",
            "dependencies": [dependency_id],
            "approval_required": False,
        },
    )
    assert dependent_response.status_code == 201

    response = client.get(
        f"/projects/{project_id}/tasks/ready"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["ready_count"] == 1
    assert data["tasks"][0]["title"] == "First task"
    assert all(
        task["title"] != "Dependent task"
        for task in data["tasks"]
    )


def test_list_ready_tasks_for_missing_project():
    response = client.get(
        "/projects/999999999/tasks/ready"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

def test_task_cannot_be_completed_before_dependencies_complete():
    project_response = client.post(
        "/projects",
        json={"name": "Completion Dependency Test"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    dependency_response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Backend task"},
    )
    assert dependency_response.status_code == 201
    dependency_id = dependency_response.json()["id"]

    task_response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "Frontend task",
            "dependencies": [dependency_id],
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 409
    assert "Complete all task dependencies" in response.json()["detail"]
