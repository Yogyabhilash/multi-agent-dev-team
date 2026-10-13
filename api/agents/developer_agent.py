
from api.agents.base_agent import AgentResult, BaseAgent
from api.agents.ollama_client import OllamaClient


class DeveloperAgent(BaseAgent):
    """Generate code or technical solutions using Ollama."""

    def __init__(self, ollama_client: OllamaClient | None = None):
        self.ollama_client = ollama_client or OllamaClient()

    def execute(self, title: str, description: str) -> AgentResult:
        """Generate a response for the given task."""

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

        # RoleAwareAgent can provide its own role and instructions.
        # A regular DeveloperAgent defaults to the developer role.
        role = getattr(self, "role", "developer")
        role_instructions = getattr(
            self,
            "role_instructions",
            "Generate a software implementation that addresses the task.",
        )

        prompt = f"""
You are acting as the {role} on a software development team.

Task title:
{title}

Task description:
{description}

Role-specific instructions:
{role_instructions}

General instructions:
- Address the task requirements directly.
- Use clear, maintainable, and well-structured output.
- Include relevant filenames when appropriate.
- Explain important implementation or design decisions briefly.
- Identify assumptions or missing requirements where relevant.
- Do not claim that code was executed or tests were run.
- Return your output and explanation clearly.
"""

        try:
            generated_output = self.ollama_client.generate(prompt)

            if not generated_output or not generated_output.strip():
                return AgentResult(
                    success=False,
                    output="",
                    error="Ollama returned an empty response.",
                )

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
