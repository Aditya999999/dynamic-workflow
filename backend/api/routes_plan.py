from fastapi import APIRouter, Depends, status, HTTPException
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
    state = await orchestrator.create_and_plan_workflow(
        query=req.query,
        workspace_id=req.workspace_id,
        user_id=user_id,
        initial_context=req.initial_context
    )

    if state.status == "failed" and (not state.nodes or state.error_message):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=state.error_message or (
                "Your request appears to be outside the scope of Software Development Life Cycle (SDLC) workflows. "
                "The Dynamic Workflow Orchestrator handles SDLC tasks such as Requirements Analysis (BRD), "
                "Architecture Design, Sprint Planning, Microservice Development, and QA/Test Strategy. "
                "Please provide a software engineering requirement or task."
            )
        )

    return state
