import json
import os
import re
from pathlib import Path
from models.agents import AgentRegistrySchema, AgentDefinition, AgentEndpoint
from config.settings import get_settings


class AgentRegistry:
    def __init__(self, registry_file_path: str | None = None):
        settings = get_settings()
        self.registry_path = registry_file_path or settings.dwf_agent_registry_path
        self._agents_map: dict[str, AgentDefinition] = {}
        self.load()

    def _substitute_env_vars(self, data: str) -> str:
        pattern = re.compile(r"\$\{([A-Za-z0-9_]+)\}")
        settings = get_settings()

        def replace_match(match):
            var_name = match.group(1)
            # Check os.environ first, then settings
            if var_name in os.environ:
                return os.environ[var_name]
            attr_name = var_name.lower()
            if hasattr(settings, attr_name):
                return str(getattr(settings, attr_name))
            return match.group(0)

        return pattern.sub(replace_match, data)

    def load(self) -> None:
        path = Path(self.registry_path)
        if not path.is_absolute():
            # Resolve relative to backend directory
            base_dir = Path(__file__).resolve().parent.parent
            path = base_dir / self.registry_path

        if not path.exists():
            raise FileNotFoundError(f"Agent registry file not found at {path}")

        raw_content = path.read_text(encoding="utf-8")
        interpolated = self._substitute_env_vars(raw_content)
        parsed_data = json.loads(interpolated)
        schema = AgentRegistrySchema(**parsed_data)

        self._agents_map = {agent.agent_id: agent for agent in schema.agents}

    def get_agent(self, agent_id: str) -> AgentDefinition | None:
        return self._agents_map.get(agent_id)

    def list_agents(self) -> list[AgentDefinition]:
        return list(self._agents_map.values())

    def get_endpoint(self, agent_id: str, endpoint_name: str) -> AgentEndpoint | None:
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        for ep in agent.endpoints.task + agent.endpoints.lifecycle + agent.endpoints.admin:
            if ep.name == endpoint_name:
                return ep
        return None

    def get_base_url(self, agent_id: str, env: str = "local") -> str:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")
        binding = agent.environment_bindings.get(env) or agent.environment_bindings.get("local")
        if not binding:
            raise ValueError(f"No environment binding for agent {agent_id} in {env}")
        return binding.base_url.rstrip("/")

    def supports_task(self, agent_id: str, task_type: str) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        return task_type in agent.supported_task_types or any(ep.name == task_type for ep in agent.endpoints.task)


_registry_instance: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance
