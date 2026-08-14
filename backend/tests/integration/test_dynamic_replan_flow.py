import pytest
from domain.orchestrator import get_workflow_orchestrator
from services.workflow_repository import get_workflow_repository


@pytest.mark.asyncio
async def test_dynamic_replan_execution_flow():
    orchestrator = get_workflow_orchestrator()
    wf_repo = get_workflow_repository()

    query = "Design payment platform with dynamic reconciliation"
    state = await orchestrator.create_and_plan_workflow(query=query)

    # Set Architect node to trigger dynamic replanning scenario
    arch_node = next(n for n in state.nodes if n.agent_id == "architect")
    arch_node.input_data["mock_scenario"] = "dynamic_replan"
    await wf_repo.save_workflow(state)

    # Run execution loop
    await orchestrator._run_execution_loop(state.workflow_id, auto_approve_hitl=True)

    final_state = await wf_repo.get_workflow(state.workflow_id)
    assert final_state is not None
    assert final_state.status == "completed"
    assert final_state.plan_version >= 2
    assert final_state.replan_count >= 1

    # Verify revision nodes executed and completed
    clarify_node = next((n for n in final_state.nodes if "Clarification" in n.display_name), None)
    assert clarify_node is not None
    assert clarify_node.status == "completed"
