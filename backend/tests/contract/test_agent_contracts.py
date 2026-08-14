import pytest
from services.mock_agent_client import MockAgentClient


@pytest.mark.asyncio
async def test_ba_agent_mock_contract():
    mock_client = MockAgentClient()
    res = await mock_client.invoke_agent("business-analyst", "dynamic_workflow_ba_task", {"prompt": "Create BRD"})
    assert res["success"] is True
    assert "data" in res
    assert "artifact_content" in res["data"]
    assert "BRD" in res["data"]["artifact_name"]


@pytest.mark.asyncio
async def test_architect_agent_mock_contract():
    mock_client = MockAgentClient()
    res = await mock_client.invoke_agent("architect", "send_message", {"user_message": "Design architecture"})
    assert res["success"] is True
    assert "Architecture" in res["data"]["artifact_name"]
    assert "mermaid" in res["data"]["artifact_content"]


@pytest.mark.asyncio
async def test_developer_agent_mock_contract():
    mock_client = MockAgentClient()
    res = await mock_client.invoke_agent("developer", "handle_dev_message", {"message": "Generate code"})
    assert res["success"] is True
    assert res["data"]["artifact_type"] == "code"


@pytest.mark.asyncio
async def test_po_agent_mock_contract():
    mock_client = MockAgentClient()
    res = await mock_client.invoke_agent("product-owner", "sprint_planning", {"prompt": "Sprint plan"})
    assert res["success"] is True
    assert "Sprint" in res["data"]["artifact_name"]


@pytest.mark.asyncio
async def test_qe_agent_mock_contract():
    mock_client = MockAgentClient()
    res = await mock_client.invoke_agent("qe", "generate_test_strategy", {"requirements": "Test plan"})
    assert res["success"] is True
    assert "QE" in res["data"]["artifact_name"]
