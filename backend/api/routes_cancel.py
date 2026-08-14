from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models.workflow import WorkflowState
from domain.orchestrator import WorkflowOrchestrator, get_workflow_orchestrator
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Workflow Cancellation"])


class CancelRequest(BaseModel):
    reason: str = "User requested cancellation"


@router.post("/{workflow_id}/cancel", response_model=WorkflowState)
async def cancel_workflow(
    workflow_id: str,
    req: CancelRequest = CancelRequest(),
    current_user: dict = Depends(get_current_user),
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator)
):
    """Cancels active workflow execution."""
    try:
        return await orchestrator.cancel_workflow(workflow_id, req.reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
