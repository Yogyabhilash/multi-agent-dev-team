
from unittest.mock import Mock

from api.agents.base_agent import AgentResult
from api.agents.developer_agent import DeveloperAgent


def test_developer_agent_returns_generated_code():
    ollama_client = Mock()
    ollama_client.generate.return_value = "def hello():\n    return 'Hello'"

    agent = DeveloperAgent(ollama_client=ollama_client)

    result = agent.execute(
        title="Create hello function",
        description="Write a Python function that returns Hello.",
    )

    assert result.success is True
    assert "def hello():" in result.output
    assert result.error is None
    ollama_client.generate.assert_called_once()


def test_developer_agent_rejects_empty_title():
    ollama_client = Mock()
    agent = DeveloperAgent(ollama_client=ollama_client)

    result = agent.execute(
        title="   ",
        description="Write a Python function.",
    )

    assert result == AgentResult(
        success=False,
        output="",
        error="Task title cannot be empty.",
    )
    ollama_client.generate.assert_not_called()


def test_developer_agent_rejects_empty_description():
    ollama_client = Mock()
    agent = DeveloperAgent(ollama_client=ollama_client)

    result = agent.execute(
        title="Create hello function",
        description=" ",
    )

    assert result == AgentResult(
        success=False,
        output="",
        error="Task description cannot be empty.",
    )
    ollama_client.generate.assert_not_called()


def test_developer_agent_handles_ollama_failure():
    ollama_client = Mock()
    ollama_client.generate.side_effect = RuntimeError("Model unavailable")

    agent = DeveloperAgent(ollama_client=ollama_client)

    result = agent.execute(
        title="Create hello function",
        description="Write a Python function.",
    )

    assert result.success is False
    assert result.output == ""
    assert result.error == "Code generation failed: Model unavailable"
