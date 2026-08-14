from typing import Any
from services.agent_registry import AgentRegistry, get_agent_registry


class SkillManager:
    """Manages skill capabilities and prompts associated with registered agents."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or get_agent_registry()

    def get_agent_capabilities(self, agent_id: str) -> list[str]:
        agent = self.registry.get_agent(agent_id)
        return agent.capabilities if agent else []

    def get_supported_skills(self) -> dict[str, list[str]]:
        return {agent.agent_id: agent.capabilities for agent in self.registry.list_agents()}
