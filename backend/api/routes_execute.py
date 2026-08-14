from fastapi import APIRouter, Depends, status, HTTPException
from models.workflow import ExecuteWorkflowRequest, WorkflowExecutionResponse
from domain.orchestrator import WorkflowOrchestrator, get_workflow_orchestrator
from services.workflow_repository import WorkflowRepository, get_workflow_repository
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Workflow Execution"])


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: str,
    req: ExecuteWorkflowRequest,
    current_user: dict = Depends(get_current_user),
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    wf_repo: WorkflowRepository = Depends(get_workflow_repository)
):
    """Starts background execution for the planned workflow and immediately returns 202 Accepted."""
    state = await wf_repo.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")

    if state.status not in ["planned", "draft", "awaiting_approval", "failed"]:
        raise HTTPException(status_code=400, detail=f"Workflow {workflow_id} cannot be executed from status '{state.status}'.")

    # Launch execution loop in background
    await orchestrator.execute_workflow_async(workflow_id, auto_approve_hitl=req.auto_approve_hitl)

    return WorkflowExecutionResponse(
        status="accepted",
        workflow_id=workflow_id,
        message="Workflow execution started in background. Follow updates via SSE event stream.",
        plan_version=state.plan_version
    )
