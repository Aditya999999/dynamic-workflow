import pytest
from domain.schema_adapter import AgentPayloadSchemaAdapter
from models.agents import AgentEndpoint
from models.artifacts import ArtifactRef


def test_schema_adapter_auto_populates_required_fields_and_feed():
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
                "agent_feed": {"type": "array", "items": {"type": "string"}},
                "language": {"type": "string", "minLength": 1}
            },
            "required": ["conversation_id", "workspace_id", "user_message", "agent_feed"]
        }
    )

    art1 = ArtifactRef(
        artifact_id="art-123456",
        name="BRD_Document.md",
        artifact_type="markdown",
        summary="Business Requirements Document for online platform"
    )

    raw_input = {"prompt": "Design high-level architecture in Python"}
    context = {
        "workspace_id": "ws_12345",
        "workflow_id": "wf_67890",
        "artifacts": [art1],
        "depends_on": ["node-1-business-analyst"]
    }

    adapted = AgentPayloadSchemaAdapter.adapt_payload(
        endpoint=endpoint,
        input_data=raw_input,
        context=context,
        workflow_id="wf_67890",
        node_id="node-2-architect",
        agent_id="architect"
    )

    # Verify all required fields were resolved and populated seamlessly
    assert adapted["conversation_id"] == "wf_67890"
    assert adapted["workspace_id"] == "ws_12345"
    assert adapted["user_message"] == "Design high-level architecture in Python"
    assert adapted["agent_id"] == "architect"
    assert adapted["language"] == "Python"

    # Verify agent_feed contains prior artifact and BRD references
    feed = adapted["agent_feed"]
    assert isinstance(feed, list)
    assert len(feed) > 0
    assert "art-123456" in feed
    assert "BRD_Document.md" in feed
    assert "brd" in feed
    assert "node-1-business-analyst" in feed
