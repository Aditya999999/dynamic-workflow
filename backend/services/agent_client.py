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
        Handles automatic payload schema adaptation and asynchronous status polling.
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

        from domain.schema_adapter import AgentPayloadSchemaAdapter

        # Adapt and validate payload against endpoint request_schema
        adapted_payload = AgentPayloadSchemaAdapter.adapt_payload(
            endpoint=endpoint,
            input_data=input_data,
            context=context,
            workflow_id=workflow_id,
            node_id=node_id,
            agent_id=agent_id
        )

        headers = {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
            "X-Workflow-ID": workflow_id or "",
            "X-Node-ID": node_id or "",
        }

        if agent.authentication_scheme == "bearer_jwt" and self.settings.jwt_secret:
            headers["Authorization"] = f"Bearer {self.settings.jwt_secret}"

        # Execute HTTP call with retry logic
        max_retries = 3
        backoff = 0.5

        async with httpx.AsyncClient(timeout=endpoint.timeout_seconds) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Calling live agent {agent_id} at {url} (Attempt {attempt}/{max_retries}) with payload: {list(adapted_payload.keys())}")
                    if endpoint.method.upper() == "GET":
                        response = await client.get(url, params=adapted_payload, headers=headers)
                    else:
                        response = await client.post(url, json=adapted_payload, headers=headers)

                    if response.status_code >= 500 and attempt < max_retries:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    response.raise_for_status()
                    res_json = response.json()

                    # Universal async status detection: if the response indicates queued/processing status
                    is_queued = isinstance(res_json, dict) and (
                        res_json.get("status") in ["queued", "in_progress", "pending", "processing"]
                        or (res_json.get("job_id") and not res_json.get("result") and not res_json.get("output") and not res_json.get("data"))
                    )

                    if is_queued:
                        job_id = res_json.get("job_id") or res_json.get("id")
                        status_route = self._resolve_status_route_for_agent(agent, endpoint)
                        if job_id and status_route:
                            logger.info(f"Response indicates queued job '{job_id}' for agent '{agent_id}'. Polling status endpoint '{status_route}'...")
                            return await self._poll_async_job(
                                client=client,
                                base_url=base_url,
                                status_route=status_route,
                                job_id=str(job_id),
                                headers=headers,
                                context=context
                            )

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

    def _resolve_status_route_for_agent(self, agent: Any, current_endpoint: Any) -> str | None:
        """Finds the registered status endpoint for the specific agent from agents.json."""
        if getattr(current_endpoint, "status_route", None):
            return current_endpoint.status_route

        # Check lifecycle endpoints for a status route
        for ep in agent.endpoints.lifecycle:
            if any(term in ep.name.lower() or term in ep.route.lower() for term in ["status", "job"]):
                return ep.route

        # Check other task endpoints
        for ep in agent.endpoints.task:
            if getattr(ep, "status_route", None):
                return ep.status_route

        return None

    async def _poll_async_job(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        status_route: str,
        job_id: str,
        headers: dict[str, str],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        # Support route template replacement (e.g. /jobs/{job_id})
        route = status_route.replace("{job_id}", job_id)
        url = f"{base_url}{route}"

        # Standard query params for status endpoints expecting query parameters (e.g. /send-message-status)
        params = {
            "job_id": job_id,
            "conversation_id": context.get("conversation_id") or context.get("workflow_id") or "",
            "workspace_id": context.get("workspace_id") or "default_workspace"
        }

        max_polls = 45
        for poll_idx in range(1, max_polls + 1):
            await asyncio.sleep(2.0)
            res = await client.get(url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                status = str(data.get("status", "")).lower()
                logger.info(f"Async poll #{poll_idx} for job {job_id}: status='{status}'")

                if status in ["completed", "success", "done"]:
                    return data
                elif status in ["failed", "error"]:
                    err_msg = data.get("error") or data.get("message") or "Unknown error"
                    raise AgentExecutionError(f"Async job {job_id} failed on remote agent: {err_msg}", agent_id="async_job")
                elif status in ["queued", "processing", "in_progress", "pending"]:
                    continue
                else:
                    # If response does not have status field or returned actual content
                    if data.get("result") or data.get("output") or data.get("data") or data.get("response"):
                        return data

        raise TimeoutError(f"Async job {job_id} timed out after {max_polls * 2} seconds on {url}")


_agent_client_instance: AgentClient | None = None


def get_agent_client() -> AgentClient:
    global _agent_client_instance
    if _agent_client_instance is None:
        _agent_client_instance = AgentClient()
    return _agent_client_instance
