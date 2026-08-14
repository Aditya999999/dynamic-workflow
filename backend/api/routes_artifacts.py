from fastapi import APIRouter, Depends, HTTPException, Query
from models.artifacts import ArtifactContentResponse
from services.artifact_store import ArtifactStore, get_artifact_store
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Artifacts"])


@router.get("/{workflow_id}/artifacts/{artifact_id}", response_model=ArtifactContentResponse)
async def get_artifact(
    workflow_id: str,
    artifact_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100000, ge=1),
    artifact_store: ArtifactStore = Depends(get_artifact_store),
    current_user: dict = Depends(get_current_user)
):
    """Retrieves artifact content and metadata with pagination/section support."""
    res = await artifact_store.read_artifact_section(artifact_id, offset=offset, limit=limit)
    if not res:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found.")
    return res
