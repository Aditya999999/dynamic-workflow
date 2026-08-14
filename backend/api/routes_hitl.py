from fastapi import APIRouter, Depends, HTTPException, status
from models.hitl import ResumePayload, ApprovalResolution
from models.workflow import WorkflowState
from domain.orchestrator import WorkflowOrchestrator, get_workflow_orchestrator
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["HITL Approvals"])


@router.post("/{workflow_id}/hitl/resume", response_model=WorkflowState)
async def resume_hitl_approval(
    workflow_id: str,
    payload: ResumePayload,
    current_user: dict = Depends(get_current_user),
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator)
):
    """Submits human approval, edit, or rejection to resume a paused workflow."""
    resolution = ApprovalResolution(
        decision=payload.decision,
        feedback=payload.feedback,
        edited_data=payload.edited_data,
        user_id=current_user.get("user_id", "default_user")
    )
    try:
        return await orchestrator.resume_hitl(workflow_id, resolution)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
