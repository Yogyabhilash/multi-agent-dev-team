from api.agents.developer_agent import DeveloperAgent
from api.agents.ollama_client import OllamaClient


ROLE_INSTRUCTIONS = {
    "planner": (
        "Break project requirements into small, ordered tasks. "
        "Identify dependencies and assign suitable roles."
    ),
    "architect": (
        "Focus on system architecture, component boundaries, data flow, "
        "design decisions, and maintainability."
    ),
    "backend": (
        "Focus on server-side logic, APIs, business rules, database access, "
        "validation, and error handling."
    ),
    "frontend": (
        "Focus on user interfaces, usability, frontend components, "
        "API integration, and client-side validation."
    ),
    "qa": (
        "Focus on test cases, edge cases, expected results, regression risks, "
        "and reproducible verification steps. Do not claim tests were run."
    ),
    "devops": (
        "Focus on development environments, configuration, CI/CD, deployment, "
        "logging, monitoring, and operational reliability."
    ),
}


class RoleAwareAgent(DeveloperAgent):
    """Reuse Ollama-based generation with instructions for a specific role."""

    def __init__(
        self,
        role: str,
        ollama_client: OllamaClient | None = None,
    ):
        normalized_role = role.strip().lower()

        if normalized_role not in ROLE_INSTRUCTIONS:
            raise ValueError(f"Unsupported agent role: {role}")

        super().__init__(ollama_client=ollama_client)
        self.role = normalized_role
        self.role_instructions = ROLE_INSTRUCTIONS[normalized_role]