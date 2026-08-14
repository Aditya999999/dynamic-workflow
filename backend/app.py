import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from services.mongo import get_mongo_manager
from services.agent_registry import get_agent_registry
from api import (
    plan_router,
    execute_router,
    workflow_router,
    events_router,
    hitl_router,
    cancel_router,
    artifacts_router,
    agents_router,
    health_router
)
from mocks import ba_router, architect_router, developer_router, po_router, qe_router
from models.errors import WorkflowError, PolicyViolationError, AgentExecutionError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Dynamic Workflow Orchestrator V5...")
    settings = get_settings()
    get_agent_registry()
    mongo = get_mongo_manager()
    await mongo.connect()
    logger.info(f"Orchestrator ready on {settings.app_host}:{settings.app_port} (Env: {settings.app_env})")
    yield
    # Shutdown
    logger.info("Shutting down Orchestrator...")
    await mongo.disconnect()


app = FastAPI(
    title="Dynamic Workflow Orchestrator V5 (Deep Agent Architecture)",
    version="5.0.0",
    description="Greenfield + Office-Portable Dynamic Multi-Agent Workflow Orchestration Platform",
    lifespan=lifespan
)

# CORS middleware for local and office frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(PolicyViolationError)
async def policy_violation_handler(request: Request, exc: PolicyViolationError):
    return JSONResponse(
        status_code=400,
        content={"error": "POLICY_VIOLATION", "message": exc.message, "details": exc.details}
    )


@app.exception_handler(AgentExecutionError)
async def agent_execution_error_handler(request: Request, exc: AgentExecutionError):
    return JSONResponse(
        status_code=502,
        content={"error": "AGENT_EXECUTION_ERROR", "message": exc.message, "details": exc.details}
    )


@app.exception_handler(WorkflowError)
async def workflow_error_handler(request: Request, exc: WorkflowError):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message, "details": exc.details}
    )


# Mount main orchestrator routes
app.include_router(plan_router)
app.include_router(execute_router)
app.include_router(workflow_router)
app.include_router(events_router)
app.include_router(hitl_router)
app.include_router(cancel_router)
app.include_router(artifacts_router)
app.include_router(agents_router)
app.include_router(health_router)

# Mount mock agent microservices for standalone testing
app.include_router(ba_router, prefix="/mock/ba")
app.include_router(architect_router, prefix="/mock/architect")
app.include_router(developer_router, prefix="/mock/developer")
app.include_router(po_router, prefix="/mock/po")
app.include_router(qe_router, prefix="/mock/qe")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app:app", host=settings.app_host, port=settings.app_port, reload=True)
