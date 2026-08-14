from fastapi import APIRouter, Depends, HTTPException, status
from models.workflow import WorkflowState
from models.graph import WorkflowGraphModel
from domain.workflow_graph import WorkflowGraphBuilder
from services.workflow_repository import WorkflowRepository, get_workflow_repository
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Workflow State"])


@router.get("", response_model=list[WorkflowState])
async def list_workflows(
    limit: int = 20,
    wf_repo: WorkflowRepository = Depends(get_workflow_repository),
    current_user: dict = Depends(get_current_user)
):
    return await wf_repo.list_workflows(limit=limit)


@router.get("/{workflow_id}", response_model=WorkflowState)
async def get_workflow(
    workflow_id: str,
    wf_repo: WorkflowRepository = Depends(get_workflow_repository),
    current_user: dict = Depends(get_current_user)
):
    state = await wf_repo.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")
    return state


@router.get("/{workflow_id}/graph", response_model=WorkflowGraphModel)
async def get_workflow_graph(
    workflow_id: str,
    wf_repo: WorkflowRepository = Depends(get_workflow_repository),
    current_user: dict = Depends(get_current_user)
):
    state = await wf_repo.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")
    return WorkflowGraphBuilder.build_xyflow_graph(state)
