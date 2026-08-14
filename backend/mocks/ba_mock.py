from fastapi import FastAPI, APIRouter, Request, status
from services.mock_agent_client import MockAgentClient

ba_router = APIRouter(prefix="/api", tags=["BA Agent Mock"])
mock_client = MockAgentClient()


@ba_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ba-rest-api", "version": "1.0.0"}


@ba_router.post("/create-session")
async def create_session():
    return {"success": True, "data": {"session_id": "ba_sess_1001"}}


@ba_router.post("/dynamic-workflow/ba-task")
async def dynamic_workflow_ba_task(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("business-analyst", "dynamic_workflow_ba_task", payload)


@ba_router.post("/create-user-stories")
async def create_user_stories(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("business-analyst", "create_user_stories", payload)


@ba_router.post("/handle-ba-message")
async def handle_ba_message(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("business-analyst", "handle_ba_message", payload)
