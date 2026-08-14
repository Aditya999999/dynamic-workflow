from fastapi import APIRouter, Request
from services.mock_agent_client import MockAgentClient

developer_router = APIRouter(prefix="/api", tags=["Developer Agent Mock"])
mock_client = MockAgentClient()


@developer_router.get("/health")
async def health():
    return {"status": "healthy", "service": "dev-rest-api", "version": "1.0.0"}


@developer_router.post("/handle-dev-message")
async def handle_dev_message(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("developer", "handle_dev_message", payload)


@developer_router.post("/async/handle-dev-message")
async def async_handle_dev_message(request: Request):
    return {"status": "accepted", "job_id": "job_dev_101"}


@developer_router.get("/jobs/{job_id}")
async def jobs_status(job_id: str):
    return {"status": "completed", "job_id": job_id, "data": {"status": "success"}}
