# Agent Registry
# Dynamic discovery and factory for crew agents


from ..providers import BaseProvider

from .base import BaseAgent
from .commander import CommanderAgent
from .dev import DeveloperAgent
from .planner import PlannerAgent
from .reviewer import ReviewerAgent
from .ux import UXAgent


class AgentRegistry:
    """Registry for managing crew agents."""

    _agents: dict[str, type[BaseAgent]] = {}

    @classmethod
    def register(cls, role: str, agent_class: type[BaseAgent]):
        """Register an agent class."""
        cls._agents[role] = agent_class

    @classmethod
    def create_agent(cls, role: str, provider: BaseProvider, model: str, **kwargs) -> BaseAgent:
        """Create agent instance."""
        if role not in cls._agents:
            raise ValueError(f"Unknown agent role: {role}")

        return cls._agents[role](provider, model, **kwargs)

    @classmethod
    def create_crew(cls, provider: BaseProvider, model: str, **kwargs) -> dict[str, BaseAgent]:
        """Create standard crew with all registered agents."""
        crew = {}
        for role in cls._agents:
            crew[role] = cls.create_agent(role, provider, model, **kwargs)
        return crew

    @classmethod
    def list_agents(cls) -> list[str]:
        """Get list of registered agent roles."""
        return list(cls._agents.keys())

    @classmethod
    def get_agent_info(cls) -> dict[str, dict]:
        """Get information about registered agents."""
        info = {}
        for role, agent_class in cls._agents.items():
            # Create temporary instance to get config
            try:
                temp_config = agent_class.__init__.__defaults__
                info[role] = {
                    "class": agent_class.__name__,
                    "role": role,
                    "description": agent_class.__doc__ or f"{role} agent",
                }
            except:
                info[role] = {
                    "class": agent_class.__name__,
                    "role": role,
                    "description": f"{role} agent",
                }
        return info


# Register built-in agents
AgentRegistry.register("UX", UXAgent)
AgentRegistry.register("Planner", PlannerAgent)
AgentRegistry.register("Developer", DeveloperAgent)
AgentRegistry.register("Reviewer", ReviewerAgent)
AgentRegistry.register("Commander", CommanderAgent)


def create_crew(provider: BaseProvider, model: str, **kwargs) -> dict[str, BaseAgent]:
    """Convenience function to create standard crew."""
    return AgentRegistry.create_crew(provider, model, **kwargs)


def list_available_agents() -> list[str]:
    """Convenience function to list available agents."""
    return AgentRegistry.list_agents()
