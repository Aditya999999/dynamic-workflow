import pytest
from domain.schema_adapter import AgentPayloadSchemaAdapter
from models.agents import AgentEndpoint


def test_schema_adapter_auto_populates_required_fields():
    endpoint = AgentEndpoint(
        name="send_message",
        route="/send-message",
        method="POST",
        request_schema={
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string"},
                "workspace_id": {"type": "string"},
                "user_message": {"type": "string"},
                "agent_id": {"type": "string"},
                "agent_feed": {"type": "array"}
            },
            "required": ["conversation_id", "workspace_id", "user_message"]
        }
    )

    # Input data provides 'prompt' instead of 'user_message' and omits conversation_id/workspace_id
    raw_input = {"prompt": "Design high-level architecture"}
    context = {"workspace_id": "ws_12345", "workflow_id": "wf_67890"}

    adapted = AgentPayloadSchemaAdapter.adapt_payload(
        endpoint=endpoint,
        input_data=raw_input,
        context=context,
        workflow_id="wf_67890",
        node_id="node-2-arch",
        agent_id="architect"
    )

    # Verify all required fields were resolved and populated seamlessly
    assert adapted["conversation_id"] == "wf_67890"
    assert adapted["workspace_id"] == "ws_12345"
    assert adapted["user_message"] == "Design high-level architecture"
    assert adapted["agent_feed"] == []
    assert adapted["agent_id"] == "architect"
