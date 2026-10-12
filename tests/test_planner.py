
from fastapi.testclient import TestClient

from api.main import app
from api.agents.planner import PlannerAgent


client = TestClient(app)

def test_planner_creates_tasks_for_login_website():
    from api.agents.planner import PlannerAgent

    plan = PlannerAgent().create_plan(
        "Demo Website",
        "Build a website with login and a dashboard",
    )

    assert plan.project_name == "Demo Website"
    assert len(plan.tasks) == 6

    assert plan.tasks[0].dependencies == []
    assert plan.tasks[1].dependencies == [1]

    titles = [task.title for task in plan.tasks]
    assert "Implement authentication" in titles
    assert "Implement the backend" in titles
    assert "Build the frontend" in titles

    test_task = next(
        task for task in plan.tasks
        if task.title == "Test the application"
    )

    assert test_task.dependencies == [4, 5]


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
    assert len(data["tasks"]) == 6

    tasks = data["tasks"]
    assert tasks[0]["dependencies"] == []
    assert tasks[1]["dependencies"] == [tasks[0]["id"]]
    
    test_task = next(
        task for task in tasks
        if task["title"] == "Test the application"
    )

    backend_task = next(
        task for task in tasks
        if task["title"] == "Implement the backend"
    )

    frontend_task = next(
        task for task in tasks
        if task["title"] == "Build the frontend"
    )

    assert set(test_task["dependencies"]) == {
        backend_task["id"],
        frontend_task["id"],
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


def test_planner_tasks_have_valid_dependencies():
    planner = PlannerAgent()
    plan = planner.create_plan(
        "Demo Website",
        "Build a website with login and a dashboard",
    )

    task_numbers = set(range(1, len(plan.tasks) + 1))

    for task_number, task in enumerate(plan.tasks, start=1):
        assert task.title.strip()
        assert 1 <= task.priority <= 5

        # Dependencies must refer to earlier tasks.
        for dependency in task.dependencies:
            assert dependency in task_numbers
            assert dependency < task_number


def test_planner_frontend_and_backend_depend_on_architecture():
    planner = PlannerAgent()
    plan = planner.create_plan(
        "Demo Website",
        "Build a website with login and a dashboard",
    )

    task_numbers = {
        task.title: number
        for number, task in enumerate(plan.tasks, start=1)
    }

    assert plan.tasks[task_numbers["Implement the backend"] - 1].dependencies == [
        task_numbers["Design the architecture"]
    ]

    assert plan.tasks[task_numbers["Build the frontend"] - 1].dependencies == [
        task_numbers["Design the architecture"]
    ]

def test_planner_adds_ecommerce_task():
    planner = PlannerAgent()
    plan = planner.create_plan(
        "Online Store",
        "Build an e-commerce website with a product catalog and shopping cart"
    )

    titles = [task.title for task in plan.tasks]

    assert "Implement product and order features" in titles
    assert "Implement the backend" in titles
    assert "Build the frontend" in titles


def test_planner_creates_basic_website_plan():
    planner = PlannerAgent()
    plan = planner.create_plan(
        "Portfolio Website",
        "Build a personal portfolio website"
    )

    titles = [task.title for task in plan.tasks]

    assert "Analyze requirements" in titles
    assert "Design the architecture" in titles
    assert "Implement the backend" in titles
    assert "Build the frontend" in titles
    assert "Test the application" in titles
    assert "Implement authentication" not in titles
