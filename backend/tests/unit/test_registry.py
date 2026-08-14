import pytest
from services.agent_registry import AgentRegistry


def test_agent_registry_loads_all_five_agents():
    registry = AgentRegistry()
    agents = registry.list_agents()
    agent_ids = [a.agent_id for a in agents]

    assert "business-analyst" in agent_ids
    assert "architect" in agent_ids
    assert "developer" in agent_ids
    assert "product-owner" in agent_ids
    assert "qe" in agent_ids


def test_agent_registry_task_support():
    registry = AgentRegistry()
    assert registry.supports_task("business-analyst", "dynamic_workflow_ba_task")
    assert registry.supports_task("architect", "send_message")
    assert registry.supports_task("developer", "handle_dev_message")
    assert registry.supports_task("product-owner", "sprint_planning")
    assert registry.supports_task("qe", "generate_test_strategy")
