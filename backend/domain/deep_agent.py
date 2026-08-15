import logging
from typing import Any
from config.settings import get_settings
from domain.agent_tools import AgentTools, get_agent_tools
from models.workflow import StandardAgentResponse

logger = logging.getLogger(__name__)

DEEP_AGENT_SYSTEM_PROMPT = """You are the Dynamic Workflow Orchestrator.

Your objective is to complete the business workflow requested by the user using registered agent task tools.

Rules:
1. Only use registered task tools.
2. Respect endpoint request_schema: ALWAYS provide all 'required' fields specified in agents.json (e.g. conversation_id, workspace_id, user_message/prompt).
3. Never invent agents or capabilities.
4. Never call lifecycle/admin operations as business tools.
5. Respect dependencies.
6. Respect human approval requirements.
7. Use artifact references rather than copying large artifacts.
8. Request additional agent work only through structured actions.
9. Do not continue indefinitely.
10. Do not claim execution succeeded without tool confirmation.
11. Prefer existing artifacts instead of regenerating them.
12. Stay within workflow limits.
13. Never expose secrets or internal credentials.
"""


class DeepAgentService:
    """Intelligent reasoning and task tool execution service for Dynamic Workflow Orchestrator."""

    def __init__(self, tools: AgentTools | None = None):
        self.settings = get_settings()
        self.tools = tools or get_agent_tools()

    async def execute_agent_task(
        self,
        agent_id: str,
        task_type: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None
    ) -> StandardAgentResponse:
        logger.info(f"DeepAgent invoking task tool for agent '{agent_id}', task '{task_type}'")
        return await self.tools.execute_task(
            agent_id=agent_id,
            task_type=task_type,
            input_data=input_data,
            context=context,
            workflow_id=workflow_id,
            node_id=node_id
        )


_deep_agent_instance: DeepAgentService | None = None


def get_deep_agent_service() -> DeepAgentService:
    global _deep_agent_instance
    if _deep_agent_instance is None:
        _deep_agent_instance = DeepAgentService()
    return _deep_agent_instance
