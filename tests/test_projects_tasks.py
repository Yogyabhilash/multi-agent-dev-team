
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
