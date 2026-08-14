from fastapi import APIRouter, Request
from services.mock_agent_client import MockAgentClient

architect_router = APIRouter(prefix="/api", tags=["Architect Agent Mock"])
mock_client = MockAgentClient()


@architect_router.get("/health")
async def health():
    return {"status": "healthy", "service": "arch-rest-api", "version": "1.0.0"}


@architect_router.post("/create-session")
async def create_session():
    return {"status": "success", "data": {"session_id": "arch_sess_2001"}}


@architect_router.post("/send-message")
async def send_message(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("architect", "send_message", payload)


@architect_router.get("/send-message-status")
async def send_message_status(job_id: str | None = None):
    return {"status": "completed", "job_id": job_id or "job_arch_1", "result": {"success": True}}


@architect_router.post("/update-design-nld")
async def update_design_nld(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("architect", "update_design_nld", payload)
