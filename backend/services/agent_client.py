import asyncio
import httpx
import uuid
import logging
from typing import Any
from config.settings import get_settings
from services.agent_registry import get_agent_registry
from services.mock_agent_client import MockAgentClient
from models.errors import AgentExecutionError

logger = logging.getLogger(__name__)


class AgentClient:
    def __init__(self, mock_client: MockAgentClient | None = None):
        self.settings = get_settings()
        self.registry = get_agent_registry()
        self.mock_client = mock_client or MockAgentClient()

    async def invoke_agent(
        self,
        agent_id: str,
        task_type: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None
    ) -> dict[str, Any]:
        """
        Invokes an agent either via HTTP (live mode) or MockAgentClient (mock mode).
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        context = context or {}

        # If running in mock mode, route directly to MockAgentClient
        if self.settings.agent_mode == "mock":
            logger.info(f"[MockMode] Invoking agent={agent_id}, task={task_type}")
            return await self.mock_client.invoke_agent(agent_id, task_type, input_data, context)

        agent = self.registry.get_agent(agent_id)
        if not agent:
            raise AgentExecutionError(f"Agent {agent_id} not registered", agent_id=agent_id)

        endpoint = self.registry.get_endpoint(agent_id, task_type)
        if not endpoint:
            # Look for default dynamic task endpoint
            endpoint_name = "dynamic_workflow_ba_task" if agent_id == "business-analyst" else "send_message"
            endpoint = self.registry.get_endpoint(agent_id, endpoint_name)

        if not endpoint or not endpoint.enabled:
            raise AgentExecutionError(f"Endpoint for task '{task_type}' on agent '{agent_id}' is unavailable", agent_id=agent_id)

        base_url = self.registry.get_base_url(agent_id, env=self.settings.app_env)
        url = f"{base_url}{endpoint.route}"

        headers = {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
            "X-Workflow-ID": workflow_id or "",
            "X-Node-ID": node_id or "",
        }

        if agent.authentication_scheme == "bearer_jwt" and self.settings.jwt_secret:
            # Attach JWT token
            headers["Authorization"] = f"Bearer {self.settings.jwt_secret}"

        # Execute HTTP call with retry logic
        max_retries = 3
        backoff = 0.5

        async with httpx.AsyncClient(timeout=endpoint.timeout_seconds) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Calling live agent {agent_id} at {url} (Attempt {attempt}/{max_retries})")
                    if endpoint.method.upper() == "GET":
                        response = await client.get(url, params=input_data, headers=headers)
                    else:
                        response = await client.post(url, json=input_data, headers=headers)

                    if response.status_code >= 500 and attempt < max_retries:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    response.raise_for_status()
                    res_json = response.json()

                    # Handle async polling if supported
                    if endpoint.async_supported and res_json.get("job_id") and endpoint.status_route:
                        job_id = res_json["job_id"]
                        return await self._poll_async_job(client, base_url, endpoint.status_route, job_id, headers)

                    return res_json

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP Error calling agent {agent_id}: {e.response.status_code} - {e.response.text}")
                    if attempt == max_retries:
                        raise AgentExecutionError(
                            f"Agent {agent_id} returned HTTP {e.response.status_code}: {e.response.text}",
                            agent_id=agent_id
                        )
                except httpx.RequestError as e:
                    logger.warning(f"Connection error calling agent {agent_id}: {str(e)}")
                    if attempt == max_retries:
                        raise AgentExecutionError(
                            f"Failed to connect to agent {agent_id}: {str(e)}",
                            agent_id=agent_id
                        )
                await asyncio.sleep(backoff)
                backoff *= 2

        raise AgentExecutionError(f"Invocation failed for agent {agent_id}", agent_id=agent_id)

    async def _poll_async_job(
        self, client: httpx.AsyncClient, base_url: str, status_route: str, job_id: str, headers: dict[str, str]
    ) -> dict[str, Any]:
        route = status_route.replace("{job_id}", job_id)
        url = f"{base_url}{route}"
        max_polls = 30
        for _ in range(max_polls):
            await asyncio.sleep(2.0)
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                status = data.get("status")
                if status in ["completed", "success"]:
                    return data
                elif status in ["failed", "error"]:
                    raise AgentExecutionError(f"Async job {job_id} failed: {data.get('error')}", agent_id="async_job")
        raise TimeoutError(f"Async job {job_id} timed out after {max_polls * 2} seconds")


_agent_client_instance: AgentClient | None = None


def get_agent_client() -> AgentClient:
    global _agent_client_instance
    if _agent_client_instance is None:
        _agent_client_instance = AgentClient()
    return _agent_client_instance
