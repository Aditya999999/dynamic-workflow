import logging
from typing import Any
from services.agent_client import AgentClient, get_agent_client
from domain.response_normalizer import ResponseNormalizer, get_response_normalizer
from models.workflow import StandardAgentResponse

logger = logging.getLogger(__name__)


class AgentTools:
    """Task tools invoked during Deep Agent orchestration."""

    def __init__(self, client: AgentClient | None = None, normalizer: ResponseNormalizer | None = None):
        self.client = client or get_agent_client()
        self.normalizer = normalizer or get_response_normalizer()

    async def execute_task(
        self,
        agent_id: str,
        task_type: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None
    ) -> StandardAgentResponse:
        logger.info(f"AgentTools executing: agent={agent_id}, task={task_type}, workflow_id={workflow_id}")
        raw_res = await self.client.invoke_agent(
            agent_id=agent_id,
            task_type=task_type,
            input_data=input_data,
            context=context,
            workflow_id=workflow_id,
            node_id=node_id
        )
        return self.normalizer.normalize(agent_id, raw_res)

    async def business_analyst_task(self, task_type: str, input_data: dict[str, Any], **kwargs) -> StandardAgentResponse:
        return await self.execute_task("business-analyst", task_type, input_data, **kwargs)

    async def architect_task(self, task_type: str, input_data: dict[str, Any], **kwargs) -> StandardAgentResponse:
        return await self.execute_task("architect", task_type, input_data, **kwargs)

    async def developer_task(self, task_type: str, input_data: dict[str, Any], **kwargs) -> StandardAgentResponse:
        return await self.execute_task("developer", task_type, input_data, **kwargs)

    async def product_owner_task(self, task_type: str, input_data: dict[str, Any], **kwargs) -> StandardAgentResponse:
        return await self.execute_task("product-owner", task_type, input_data, **kwargs)

    async def qe_task(self, task_type: str, input_data: dict[str, Any], **kwargs) -> StandardAgentResponse:
        return await self.execute_task("qe", task_type, input_data, **kwargs)


_tools_instance: AgentTools | None = None


def get_agent_tools() -> AgentTools:
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = AgentTools()
    return _tools_instance
