from fastapi import APIRouter, Request
from services.mock_agent_client import MockAgentClient

qe_router = APIRouter(prefix="/api", tags=["Quality Engineer Agent Mock"])
mock_client = MockAgentClient()


@qe_router.get("/health")
async def health():
    return {"status": "healthy", "service": "qe-rest-api", "version": "1.0.0"}


@qe_router.post("/generate-test-strategy")
async def generate_test_strategy(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("qe", "generate_test_strategy", payload)


@qe_router.post("/generate-test-cases")
async def generate_test_cases(request: Request):
    payload = await request.json()
    return await mock_client.invoke_agent("qe", "generate_test_cases", payload)
