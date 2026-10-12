
import json

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.agents.planner import PlannerAgent


client = TestClient(app)


def make_plan_response(project_name, request):
    """Create a predictable AI response for testing."""

    tasks = [
        {
            "title": "Analyze requirements",
            "description": f"Analyze requirements for: {request}",
            "assigned_agent": "planner",
            "priority": 1,
            "dependencies": [],
        },
        {
            "title": "Design the architecture",
            "description": "Design the application components.",
            "assigned_agent": "architect",
            "priority": 2,
            "dependencies": [1],
        },
        {
            "title": "Implement the backend",
            "description": "Implement APIs and business logic.",
            "assigned_agent": "backend",
            "priority": 3,
            "dependencies": [2],
        },
        {
            "title": "Build the frontend",
            "description": "Build the user interface.",
            "assigned_agent": "frontend",
            "priority": 3,
            "dependencies": [2],
        },
        {
            "title": "Test the application",
            "description": "Test the application functionality.",
            "assigned_agent": "qa",
            "priority": 2,
            "dependencies": [3, 4],
        },
    ]

    if any(
        word in request.lower()
        for word in ["login", "authentication", "sign in", "signup", "register"]
    ):
        tasks.insert(
            2,
            {
                "title": "Implement authentication",
                "description": "Implement secure user authentication.",
                "assigned_agent": "backend",
                "priority": 2,
                "dependencies": [2],
            },
        )
        # Testing now depends on the backend and frontend task numbers.
        tasks[-1]["dependencies"] = [4, 5]

    if any(
        word in request.lower()
        for word in ["e-commerce", "ecommerce", "shop", "store", "payment", "cart"]
    ):
        tasks.insert(
            -1,
            {
                "title": "Implement product and order features",
                "description": "Implement catalog, cart, and order workflows.",
                "assigned_agent": "backend",
                "priority": 3,
                "dependencies": [2],
            },
        )

    return json.dumps(
        {
            "project_name": project_name,
            "summary": f"Test plan for: {request}",
            "tasks": tasks,
        }
    )


class FakeOllamaClient:
    def __init__(self, response=None):
        self.response = response

    def generate(self, prompt):
        if self.response is None:
            raise RuntimeError("No fake response configured.")
        return self.response


def test_planner_creates_tasks_for_login_website():
    project_name = "Demo Website"
    request = "Build a website with login and a dashboard"

    planner = PlannerAgent(
        FakeOllamaClient(make_plan_response(project_name, request))
    )
    plan = planner.create_plan(project_name, request)

    assert plan.project_name == project_name
    assert len(plan.tasks) == 6

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
    planner = PlannerAgent(FakeOllamaClient())

    with pytest.raises(ValueError, match="Project name cannot be empty"):
        planner.create_plan("", "Build a website")


def test_planner_rejects_empty_request():
    planner = PlannerAgent(FakeOllamaClient())

    with pytest.raises(ValueError, match="Project request cannot be empty"):
        planner.create_plan("Demo Website", "")


def test_planner_rejects_invalid_json():
    planner = PlannerAgent(FakeOllamaClient("not valid JSON"))

    with pytest.raises(ValueError, match="invalid project plan"):
        planner.create_plan("Demo Website", "Build a website")


def test_planner_rejects_invalid_dependency():
    response = json.dumps(
        {
            "project_name": "Demo Website",
            "summary": "Test plan",
            "tasks": [
                {
                    "title": "Analyze requirements",
                    "description": "Analyze requirements.",
                    "assigned_agent": "planner",
                    "priority": 1,
                    "dependencies": [2],
                },
                {
                    "title": "Design the architecture",
                    "description": "Design components.",
                    "assigned_agent": "architect",
                    "priority": 2,
                    "dependencies": [1],
                },
                {
                    "title": "Implement the backend",
                    "description": "Implement APIs.",
                    "assigned_agent": "backend",
                    "priority": 3,
                    "dependencies": [2],
                },
                {
                    "title": "Build the frontend",
                    "description": "Build the UI.",
                    "assigned_agent": "frontend",
                    "priority": 3,
                    "dependencies": [2],
                },
            ],
        }
    )

    planner = PlannerAgent(FakeOllamaClient(response))

    with pytest.raises(ValueError, match="invalid dependency"):
        planner.create_plan("Demo Website", "Build a website")


def test_planner_rejects_unsupported_agent():
    response_data = json.loads(
        make_plan_response("Demo Website", "Build a website")
    )
    response_data["tasks"][0]["assigned_agent"] = "unknown_agent"

    planner = PlannerAgent(
        FakeOllamaClient(json.dumps(response_data))
    )

    with pytest.raises(ValueError, match="unsupported assigned agent"):
        planner.create_plan("Demo Website", "Build a website")


def test_planner_tasks_have_valid_dependencies():
    project_name = "Demo Website"
    request = "Build a website with login and a dashboard"

    planner = PlannerAgent(
        FakeOllamaClient(make_plan_response(project_name, request))
    )
    plan = planner.create_plan(project_name, request)

    for task_number, task in enumerate(plan.tasks, start=1):
        assert task.title.strip()
        assert 1 <= task.priority <= 5

        for dependency in task.dependencies:
            assert 1 <= dependency < task_number


def test_create_project_plan_api():
    project_name = "Automated Plan Test"
    request = "Build a website with login and a dashboard"

    # Replace only the planner's Ollama client for this API test.
    from api.main import PlannerAgent as MainPlannerAgent

    original_init = MainPlannerAgent.__init__

    def fake_init(self):
        self.ollama_client = FakeOllamaClient(
            make_plan_response(project_name, request)
        )

    MainPlannerAgent.__init__ = fake_init

    try:
        response = client.post(
            "/projects/plan",
            json={
                "project_name": project_name,
                "request": request,
            },
        )
    finally:
        MainPlannerAgent.__init__ = original_init

    assert response.status_code == 201
    data = response.json()
    assert data["project"]["name"] == project_name
    assert len(data["tasks"]) == 6

    tasks = data["tasks"]
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


def test_planner_adds_ecommerce_task():
    project_name = "Online Store"
    request = "Build an e-commerce website with a product catalog and shopping cart"

    planner = PlannerAgent(
        FakeOllamaClient(make_plan_response(project_name, request))
    )
    plan = planner.create_plan(project_name, request)

    titles = [task.title for task in plan.tasks]
    assert "Implement product and order features" in titles
    assert "Implement the backend" in titles
    assert "Build the frontend" in titles


def test_planner_creates_basic_website_plan():
    project_name = "Portfolio Website"
    request = "Build a personal portfolio website"

    planner = PlannerAgent(
        FakeOllamaClient(make_plan_response(project_name, request))
    )
    plan = planner.create_plan(project_name, request)

    titles = [task.title for task in plan.tasks]
    assert "Analyze requirements" in titles
    assert "Design the architecture" in titles
    assert "Implement the backend" in titles
    assert "Build the frontend" in titles
    assert "Test the application" in titles
    assert "Implement authentication" not in titles
