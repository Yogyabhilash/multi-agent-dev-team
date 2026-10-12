
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResult:
    """The result produced by an AI agent."""

    success: bool
    output: str
    error: str | None = None


class BaseAgent(ABC):
    """Common interface that all AI agents must implement."""

    @abstractmethod
    def execute(self, title: str, description: str) -> AgentResult:
        """Execute a task and return its result."""
        raise NotImplementedError
