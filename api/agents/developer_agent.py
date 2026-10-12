
from api.agents.base_agent import AgentResult, BaseAgent
from api.agents.ollama_client import OllamaClient


class DeveloperAgent(BaseAgent):
    """Generate code for a development task using Ollama."""

    def __init__(self, ollama_client: OllamaClient | None = None):
        self.ollama_client = ollama_client or OllamaClient()

    def execute(self, title: str, description: str) -> AgentResult:
        """Generate a code-oriented response for the given task."""

        if not title.strip():
            return AgentResult(
                success=False,
                output="",
                error="Task title cannot be empty.",
            )

        if not description.strip():
            return AgentResult(
                success=False,
                output="",
                error="Task description cannot be empty.",
            )

        prompt = f"""
You are a software developer working on a software project.

Task title:
{title}

Task description:
{description}

Instructions:
- Generate an implementation that addresses the task.
- Use clear, maintainable code.
- Include relevant filenames when appropriate.
- Explain important implementation decisions briefly.
- Do not claim that the code was executed or tested.
- Return the code and explanation as your output.
"""

        try:
            generated_output = self.ollama_client.generate(prompt)

            return AgentResult(
                success=True,
                output=generated_output,
            )
        except Exception as exc:
            return AgentResult(
                success=False,
                output="",
                error=f"Code generation failed: {exc}",
            )
