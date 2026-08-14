import pytest
from domain.orchestrator import get_workflow_orchestrator
from services.workflow_repository import get_workflow_repository
from models.hitl import ApprovalResolution


@pytest.mark.asyncio
async def test_hitl_interrupt_and_resume():
    orchestrator = get_workflow_orchestrator()
    wf_repo = get_workflow_repository()

    query = "Create BRD with human review"
    state = await orchestrator.create_and_plan_workflow(query=query)

    # Set BA node to require HITL scenario
    ba_node = state.nodes[0]
    ba_node.input_data["mock_scenario"] = "hitl_required"
    await wf_repo.save_workflow(state)

    # Run execution loop without auto_approve_hitl
    await orchestrator._run_execution_loop(state.workflow_id, auto_approve_hitl=False)

    paused_state = await wf_repo.get_workflow(state.workflow_id)
    assert paused_state is not None
    assert paused_state.status == "awaiting_approval"
    assert paused_state.pending_approval is not None
    assert "Human approval required" in paused_state.pending_approval.reason

    # Resume with approval
    resolution = ApprovalResolution(
        decision="approved",
        feedback="BRD approved by Product Owner"
    )
    resumed_state = await orchestrator.resume_hitl(state.workflow_id, resolution)
    assert resumed_state.pending_approval is None


@pytest.mark.asyncio
async def test_workflow_cancellation():
    orchestrator = get_workflow_orchestrator()
    wf_repo = get_workflow_repository()

    query = "Workflow to be cancelled"
    state = await orchestrator.create_and_plan_workflow(query=query)

    cancelled_state = await orchestrator.cancel_workflow(state.workflow_id, reason="User cancelled via UI")
    assert cancelled_state.status == "cancelled"
    for node in cancelled_state.nodes:
        assert node.status == "cancelled"
