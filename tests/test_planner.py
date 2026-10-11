
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_planner_creates_five_tasks():
    from api.agents.planner import PlannerAgent

    plan = PlannerAgent().create_plan(
        "Demo Website",
        "Build a website with login and a dashboard",
    )

    assert plan.project_name == "Demo Website"
    assert len(plan.tasks) == 5
    assert plan.tasks[0].dependencies == []
    assert plan.tasks[1].dependencies == [1]
    assert plan.tasks[4].dependencies == [3, 4]


def test_planner_rejects_empty_project_name():
    from api.agents.planner import PlannerAgent

    try:
        PlannerAgent().create_plan("", "Build a website")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_planner_rejects_empty_request():
    from api.agents.planner import PlannerAgent

    try:
        PlannerAgent().create_plan("Demo Website", "")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_create_project_plan_api():
    response = client.post(
        "/projects/plan",
        json={
            "project_name": "Automated Plan Test",
            "request": "Build a website with login and a dashboard",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["project"]["name"] == "Automated Plan Test"
    assert len(data["tasks"]) == 5

    tasks = data["tasks"]
    assert tasks[0]["dependencies"] == []
    assert tasks[1]["dependencies"] == [tasks[0]["id"]]
    assert set(tasks[4]["dependencies"]) == {
        tasks[2]["id"],
        tasks[3]["id"],
    }

    assert all(task["status"] == "pending" for task in tasks)
    assert all(
        task["approval_status"] == "pending"
        for task in tasks
    )


def test_create_project_plan_rejects_empty_name():
    response = client.post(
        "/projects/plan",
        json={
            "project_name": "",
            "request": "Build a website",
        },
    )

    assert response.status_code == 422
