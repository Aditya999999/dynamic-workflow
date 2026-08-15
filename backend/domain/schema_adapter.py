import logging
from typing import Any
from models.agents import AgentEndpoint

logger = logging.getLogger(__name__)


class AgentPayloadSchemaAdapter:
    """
    Adapts and validates input payloads against the agent's request_schema from agents.json.
    Automatically populates required fields (conversation_id, workspace_id, user_message, etc.)
    from runtime context, preventing HTTP 400/422 validation errors.
    """

    @classmethod
    def adapt_payload(
        cls,
        endpoint: AgentEndpoint,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None,
        agent_id: str | None = None
    ) -> dict[str, Any]:
        context = context or {}
        adapted = dict(input_data or {})

        schema = endpoint.request_schema or {}
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        # 1. Resolve core standard fields from runtime context
        resolved_workspace_id = (
            adapted.get("workspace_id")
            or context.get("workspace_id")
            or "default_workspace"
        )

        resolved_conversation_id = (
            adapted.get("conversation_id")
            or context.get("conversation_id")
            or workflow_id
            or context.get("workflow_id")
            or "default_conv"
        )

        # Resolve primary prompt / message content across aliases
        raw_message_text = (
            adapted.get("user_message")
            or adapted.get("prompt")
            or adapted.get("message")
            or adapted.get("requirements")
            or context.get("query")
            or ""
        )

        # 2. Fill standard properties defined in schema or required list
        if "workspace_id" in properties or "workspace_id" in required_fields:
            adapted["workspace_id"] = resolved_workspace_id

        if "conversation_id" in properties or "conversation_id" in required_fields:
            adapted["conversation_id"] = resolved_conversation_id

        if "user_message" in properties or "user_message" in required_fields:
            adapted["user_message"] = raw_message_text

        if "prompt" in properties or "prompt" in required_fields:
            adapted["prompt"] = raw_message_text

        if "message" in properties or "message" in required_fields:
            adapted["message"] = raw_message_text

        if "requirements" in properties or "requirements" in required_fields:
            adapted["requirements"] = raw_message_text

        if "agent_id" in properties or "agent_id" in required_fields:
            if "agent_id" not in adapted or adapted["agent_id"] is None:
                prop_type = properties.get("agent_id", {}).get("type", "string")
                adapted["agent_id"] = 1 if prop_type == "integer" else (agent_id or "1")

        if "workflow_job_id" in properties or "workflow_job_id" in required_fields:
            if "workflow_job_id" not in adapted:
                adapted["workflow_job_id"] = node_id or workflow_id

        if "agent_feed" in properties or "agent_feed" in required_fields:
            if "agent_feed" not in adapted:
                adapted["agent_feed"] = []

        # 3. Check for any remaining required fields in the schema and provide safe defaults
        for req_field in required_fields:
            if req_field not in adapted or adapted[req_field] is None:
                prop_info = properties.get(req_field, {})
                prop_type = prop_info.get("type", "string")

                if isinstance(prop_type, list):
                    prop_type = next((t for t in prop_type if t != "null"), "string")

                if prop_type == "string":
                    adapted[req_field] = context.get(req_field, "")
                elif prop_type == "array":
                    adapted[req_field] = []
                elif prop_type == "object":
                    adapted[req_field] = {}
                elif prop_type == "boolean":
                    adapted[req_field] = False
                elif prop_type in ["integer", "number"]:
                    adapted[req_field] = 0

                logger.warning(
                    f"Auto-populated missing required field '{req_field}' with default for endpoint '{endpoint.name}'"
                )

        logger.info(
            f"Adapted payload for agent='{agent_id}', endpoint='{endpoint.name}': keys={list(adapted.keys())}"
        )
        return adapted
