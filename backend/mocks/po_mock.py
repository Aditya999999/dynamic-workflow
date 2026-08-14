from fastapi import APIRouter, Request
from services.mock_agent_client import MockAgentClient

po_router = APIRouter(prefix="/api", tags=["Product Owner Agent Mock"])
mock_client = MockAgentClient()


@po_router.get("/health")
async def health():
    return {"status": "healthy", "service": "po-rest-api", "version": "1.0.0"}


@po_router.post("/sprint-planning")
async def sprint_planning(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("product-owner", "sprint_planning", payload)


@po_router.post("/prioritize-backlog")
async def prioritize_backlog(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("product-owner", "prioritize_backlog", payload)
