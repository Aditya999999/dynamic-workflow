from fastapi import APIRouter, Depends, status
from models.workflow import PlanWorkflowRequest, WorkflowState
from domain.orchestrator import WorkflowOrchestrator, get_workflow_orchestrator
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Workflow Planning"])


@router.post("/plan", response_model=WorkflowState, status_code=status.HTTP_200_OK)
async def plan_workflow(
    req: PlanWorkflowRequest,
    current_user: dict = Depends(get_current_user),
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator)
):
    """Generates an initial multi-agent plan (v1) and graph structure from a natural language request."""
    user_id = current_user.get("user_id", req.user_id)
    return await orchestrator.create_and_plan_workflow(
        query=req.query,
        workspace_id=req.workspace_id,
        user_id=user_id,
        initial_context=req.initial_context
    )
