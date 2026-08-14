import pytest
from domain.orchestrator import get_workflow_orchestrator
from services.workflow_repository import get_workflow_repository


@pytest.mark.asyncio
async def test_full_workflow_end_to_end():
    orchestrator = get_workflow_orchestrator()
    wf_repo = get_workflow_repository()

    query = "Create a BRD for an online payment platform, design the architecture, prepare implementation tasks, and create a QA strategy."
    state = await orchestrator.create_and_plan_workflow(query=query)

    assert state.status == "planned"
    assert state.plan_version == 1

    # Run execution directly (with auto_approve_hitl=True for automated test)
    await orchestrator._run_execution_loop(state.workflow_id, auto_approve_hitl=True)

    final_state = await wf_repo.get_workflow(state.workflow_id)
    assert final_state is not None
    assert final_state.status == "completed"
    assert len(final_state.artifacts) >= 4

    # Verify each node completed
    for node in final_state.nodes:
        assert node.status == "completed"
