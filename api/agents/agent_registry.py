from api.agents.base_agent import BaseAgent
from api.agents.developer_agent import DeveloperAgent
from api.agents.role_agent import RoleAwareAgent


class AgentRegistry:
    """Register and retrieve agents by their assigned names."""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        """Register an agent under a name."""
        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("Agent name cannot be empty.")

        self._agents[normalized_name] = agent

    def get(self, name: str) -> BaseAgent:
        """Retrieve a registered agent by name."""
        normalized_name = name.strip().lower()

        if normalized_name not in self._agents:
            raise ValueError(f"No agent registered for: {name}")

        return self._agents[normalized_name]

    @classmethod
    def with_default_agents(cls) -> "AgentRegistry":
        """Create a registry containing all roles supported by the planner."""
        registry = cls()
        registry.register("developer", DeveloperAgent())

        for role in (
            "planner",
            "architect",
            "backend",
            "frontend",
            "qa",
            "devops",
        ):
            registry.register(role, RoleAwareAgent(role))

        return registry