
import pytest
from unittest.mock import Mock

from api.agents.agent_registry import AgentRegistry
from api.agents.developer_agent import DeveloperAgent


def test_default_registry_contains_developer_agent():
    registry = AgentRegistry.with_default_agents()

    agent = registry.get("developer")

    assert isinstance(agent, DeveloperAgent)


def test_registry_supports_case_insensitive_names():
    registry = AgentRegistry()
    agent = Mock(spec=DeveloperAgent)

    registry.register("Developer", agent)

    assert registry.get("developer") is agent
    assert registry.get("DEVELOPER") is agent


def test_registry_rejects_empty_agent_name():
    registry = AgentRegistry()
    agent = Mock(spec=DeveloperAgent)

    with pytest.raises(ValueError, match="Agent name cannot be empty"):
        registry.register("   ", agent)


def test_registry_rejects_unknown_agent():
    registry = AgentRegistry()

    with pytest.raises(
        ValueError,
        match="No agent registered for: tester",
    ):
        registry.get("tester")


def test_registry_can_replace_registered_agent():
    registry = AgentRegistry()
    first_agent = Mock(spec=DeveloperAgent)
    second_agent = Mock(spec=DeveloperAgent)

    registry.register("developer", first_agent)
    registry.register("developer", second_agent)

    assert registry.get("developer") is second_agent
