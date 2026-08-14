from fastapi import APIRouter, Depends
from models.agents import AgentDefinition
from services.agent_registry import AgentRegistry, get_agent_registry
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Agents Registry"])


@router.get("/agents", response_model=list[AgentDefinition])
async def list_agents(
    registry: AgentRegistry = Depends(get_agent_registry),
    current_user: dict = Depends(get_current_user)
):
    """Returns the list of registered agents and their capabilities."""
    return registry.list_agents()
