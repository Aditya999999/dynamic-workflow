from fastapi import APIRouter
from config.settings import get_settings
from services.mongo import get_mongo_manager

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    mongo = get_mongo_manager()
    return {
        "status": "healthy",
        "service": "dynamic-workflow-orchestrator",
        "version": "5.0.0",
        "environment": settings.app_env,
        "agent_mode": settings.agent_mode,
        "mongodb_connected": mongo.is_connected
    }
