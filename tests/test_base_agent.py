
import pytest

from api.agents.base_agent import AgentResult, BaseAgent


def test_agent_result_success():
    result = AgentResult(
        success=True,
        output="Generated code successfully",
    )

    assert result.success is True
    assert result.output == "Generated code successfully"
    assert result.error is None


def test_agent_result_failure():
    result = AgentResult(
        success=False,
        output="",
        error="Model request failed",
    )

    assert result.success is False
    assert result.output == ""
    assert result.error == "Model request failed"


def test_base_agent_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseAgent()


def test_concrete_agent_can_implement_interface():
    class ExampleAgent(BaseAgent):
        def execute(
            self,
            title: str,
            description: str,
        ) -> AgentResult:
            return AgentResult(
                success=True,
                output=f"Completed: {title}",
            )

    agent = ExampleAgent()
    result = agent.execute(
        title="Create login page",
        description="Build a basic login page",
    )

    assert result.success is True
    assert result.output == "Completed: Create login page"
