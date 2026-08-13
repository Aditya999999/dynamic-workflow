# Deep Agents Dynamic Workflow Orchestrator V2 — End-to-End Master Implementation Specification

**Target Audience:** Coding Agent / Lead Engineers (Backend & Frontend)  
**Project Objective:** Greenfield implementation of a Deep Agents–based Multi-Agent Dynamic Workflow Orchestrator for 5 microservice agents deployed on Azure Functions (`BA`, `Architect`, `Dev`, `PO`, `QE`), complete with full React frontend integration in `Forge-X-Web`.  
**Core Architectural Constraints:**
1. **Dual Controller Parity:** Backend features a dual controller setup (`api.py` for local FastAPI testing and `function_app.py` / `functions/*` for production Azure Functions) backed by a 100% identical, shared `domain/`, `models/`, and `services/` layer.
2. **Frontend Integration:** Frontend components are built inside `src/components/DynamicWorkflowOrchestrator/` in `Forge-X-Web`, reusing existing authentication (`axiosClient.js`), token management (`authTokenManager.js`), session lifecycle (`sessionManager.js`), and routing patterns (`AppRoutes.jsx`).

---

## 1. Executive Context & Visual Reference Mapping

You are provided with visual context and system configuration screenshots:
* **`7.jpeg` (Azure Function App Portal):** Function App `forgeX-dev-fun-ba` on Linux Consumption plan, running HTTP triggers for BA workflows.
* **`8.jpeg`–`12.jpeg` (Agent API Contracts):** Endpoint worksheets for Architect, Dev, BA, and PO agents detailing REST routes, method specs, input JSON schemas, and response envelopes.
* **`1.jpeg`–`6.jpeg` (Repository & Orchestrator Flow):** High-level dynamic workflow architecture, repository folder structure, endpoint tables, MongoDB document models, phase tracking, and `agents.json` binding files.
* **`13.jpeg`–`19.jpeg` (Forge-X-Web Frontend & Auth Flow):** Visual structure of the React frontend (`Forge-X-Web`), route configurations in `AppRoutes.jsx`, environment configurations, and `axiosClient.js` JWT interceptor logic.

---

## 2. Core Architectural Principles & Guardrails

1. **Clean Architecture & SOLID Compliance:**
   * **Single Responsibility:** Backend controllers (`api.py` and `function_app.py`) **ONLY** handle HTTP parsing, JWT validation, delegation to `domain/` workflows, and Pydantic serialization. Zero business logic in controllers.
   * **Open/Closed Principle:** New agents or endpoint capabilities are registered via `registry/agents.json` and adapted via `domain/response_envelope.py` without modifying the core execution loop.
   * **Dependency Inversion:** Orchestrator logic depends on abstract interfaces (`filesystem_store`, `agent_client`, `checkpointer`) rather than direct database drivers.

2. **Deep Agents Framework Supremacy:**
   * Built on top of **Deep Agents (`langchain-deepagents`)**.
   * Replaces static precomputed DAGs with a dynamic planning loop (`planning.py` & `orchestrator_graph.py`).
   * Uses **Context Isolation**: Subagents and external microservices communicate through structured tool invocations. Large payloads (>2KB) are automatically offloaded to the virtual filesystem (`services/filesystem_store.py`), returning only an `artifact_ref` and `artifact_summary` to the planning context.

3. **Strict Validation & Error Envelopes:**
   * All backend requests, internal state transitions, and agent outputs must be strictly typed using **Pydantic V2**.
   * Errors must never leak raw 500 tracebacks. All exceptions are caught and wrapped into an `ErrorResponseEnvelope`.

---

## 3. End-to-End Repository Directory Layout

```text
dynamic-workflow-orchestrator/
├── backend/                      # BACKEND ORCHESTRATOR ENGINE
│   ├── api.py                    # Thin FastAPI controller (local dev)
│   ├── function_app.py           # Thin Azure Functions controller entrypoint (production)
│   ├── host.json                 # Azure Functions host configuration
│   ├── local.settings.json.sample# Azure Functions local environment template
│   ├── pyproject.toml / requirements.txt
│   │
│   ├── functions/                # One Azure Function binding per route (1:1 with api.py)
│   │   ├── plan_workflow.py
│   │   ├── execute_workflow.py
│   │   ├── get_workflow.py
│   │   ├── list_agents.py
│   │   ├── cancel_workflow.py
│   │   ├── hitl_resume.py
│   │   ├── get_artifact.py
│   │   └── health.py
│   │
│   ├── config/
│   │   ├── settings.py           # Unified settings via pydantic-settings
│   │   └── .env.sample           # Backend environment template
│   │
│   ├── domain/                   # Core Orchestrator Logic (Controller-Agnostic)
│   │   ├── orchestrator_graph.py # Deep Agents execution graph & state management
│   │   ├── planning.py           # Deterministic initial plan generator & dynamic replanner
│   │   ├── agent_tools.py        # Dynamic LangChain tool generator for task-category endpoints
│   │   ├── response_envelope.py  # Adapter converting raw agent payloads -> StandardAgentResponse
│   │   ├── hitl_gates.py         # Human-in-the-Loop interrupt gates & approval router
│   │   ├── skill_sync.py         # Agent capability change detector & tool refresh
│   │   └── workflow_state.py     # Deep Agents state schema (TypedDict & Pydantic)
│   │
│   ├── models/                   # Pydantic Schemas & DTOs
│   │   ├── envelope.py            # StandardAgentResponse, ErrorResponseEnvelope
│   │   ├── agent_contracts.py    # Strongly typed request/response schemas per agent
│   │   ├── workflow.py            # WorkflowPlanRequest, ExecutedStep, WorkflowDocument
│   │   └── hitl.py                # ApprovalRequest, ApprovalDecision
│   │
│   ├── services/                 # Shared Infrastructure & Middleware Clients
│   │   ├── agent_client.py       # Async HTTP invoker (handles lifecycle headers, sessions, JWT)
│   │   ├── agent_registry.py     # Multi-endpoint agent registry reader (task/lifecycle/admin)
│   │   ├── checkpointer.py       # Deep Agents checkpointer factory (Postgres / Redis)
│   │   ├── mongo_client.py       # Business workflow persistence (dwf_workflows, dwf_events)
│   │   ├── filesystem_store.py   # Virtual FS abstraction (MongoDB GridFS / Blob storage)
│   │   ├── auth.py               # JWT verification & claims decoding
│   │   ├── sse.py                # SSE streaming event formatter
│   │   └── logging.py
│   │
│   └── registry/
│       └── agents.json           # Extended multi-endpoint agent registry configuration
│
└── frontend/ Forge-X-Web/        # FRONTEND WEB APPLICATION
    └── src/
        ├── config/
        │   ├── axiosClient.js    # Pre-existing JWT interceptor & auto refresh
        │   └── config.js         # URL getters for Orchestrator & Agents
        ├── routes/
        │   ├── AppRoutes.jsx     # Route bindings for orchestrator pages
        │   └── routesPath.js     # Route paths enum
        └── components/
            └── DynamicWorkflowOrchestrator/  # Greenfield Orchestrator UI Module
                ├── OrchestratorApi.js        # API service layer (uses axiosClient)
                ├── useOrchestratorEvents.js  # Custom Hook for SSE event streaming
                ├── DynamicWorkflowOrchestratorPage.jsx
                ├── DynamicWorkflowOrchestratorExecution.jsx
                ├── QueryInput/
                │   └── QueryInput.jsx
                ├── PlanSummary/
                │   └── PlanSummary.jsx
                ├── WorkflowGraph/
                │   ├── WorkflowGraph.jsx     # @xyflow/react canvas auto-layout
                │   └── AgentNode.jsx         # Custom graph nodes with status indicators
                ├── HITLPanel/
                │   ├── PendingApprovals.jsx   # List of interrupt gates awaiting review
                │   └── ApprovalCard.jsx       # Approve / Edit / Reject controls
                └── ArtifactViewer/
                    ├── ArtifactBrowser.jsx    # Tree view over /workspace/{workflow_id}/*
                    └── ArtifactPreview.jsx    # Markdown / Mermaid / Code syntax preview
```

---

## 4. Backend Models & Controller Parity Standard

### 4.1 Standard Agent Response Envelope (`models/envelope.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal

class StandardAgentResponse(BaseModel):
    status: Literal["completed", "needs_input", "blocked", "error"]
    result: Dict[str, Any] = Field(default_factory=dict)
    artifact_ref: Optional[str] = None
    artifact_summary: Optional[str] = None
    next_action_hint: Optional[str] = "none"
    confidence: float = 1.0

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponseEnvelope(BaseModel):
    status: str = "error"
    error: ErrorDetail
    workflow_id: Optional[str] = None
```

### 4.2 Controller Parity Example

**FastAPI Controller (`api.py`):**
```python
from fastapi import FastAPI, Depends, Header
from models.workflow import PlanRequest, PlanResponse
from services.auth import verify_jwt_token
from domain.planning import create_workflow_plan

app = FastAPI(title="Dynamic Workflow Orchestrator (Local)")

@app.post("/api/dynamic-workflow/plan", response_model=PlanResponse)
async def plan_workflow(payload: PlanRequest, authorization: str = Header(None)):
    user_data = verify_jwt_token(authorization)
    return await create_workflow_plan(
        query=payload.query,
        workspace_id=payload.workspace_id,
        user_id=user_data.get("user_id")
    )
```

**Azure Functions Controller (`functions/plan_workflow.py`):**
```python
import azure.functions as func
from services.auth import verify_jwt_token
from domain.planning import create_workflow_plan
from models.envelope import ErrorResponseEnvelope, ErrorDetail

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        user_data = verify_jwt_token(req.headers.get("Authorization"))
        body = req.get_json()
        plan = await create_workflow_plan(
            query=body.get("query"),
            workspace_id=body.get("workspace_id"),
            user_id=user_data.get("user_id")
        )
        return func.HttpResponse(plan.model_dump_json(), status_code=200, mimetype="application/json")
    except Exception as e:
        err = ErrorResponseEnvelope(error=ErrorDetail(code="PLANNING_FAILED", message=str(e)))
        return func.HttpResponse(err.model_dump_json(), status_code=400, mimetype="application/json")
```

---

## 5. Frontend Architecture & Integration (`Forge-X-Web`)

### 5.1 Reused Authentication Layer (`src/config/axiosClient.js`)
All frontend API requests use `axiosClient.js`, which intercepts requests, validates auth tokens via `assertValidAuthToken()`, attaches `Bearer ${token}` to request headers, and handles HTTP 401 token refresh/redirect logic automatically.

### 5.2 Orchestrator API Client (`OrchestratorApi.js`)
```javascript
import apiClient from '../../config/axiosClient';
import { getDynamicWorkflowApiUrl } from '../../config/config';

const BASE = () => `${getDynamicWorkflowApiUrl()}/api/dynamic-workflow`;

export async function planWorkflow({ query, workspaceId, userId, idempotencyKey }) {
  const { data } = await apiClient.post(`${BASE()}/plan`, {
    query,
    workspace_id: String(workspaceId),
    user_id: String(userId || ''),
  }, {
    headers: idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {}
  });
  return data;
}

export async function executeWorkflow(workflowId) {
  const { data } = await apiClient.post(`${BASE()}/${workflowId}/execute`, {}, { timeout: 120000 });
  return data;
}

export async function resumeHITLWorkflow(workflowId, decisionData) {
  const { data } = await apiClient.post(`${BASE()}/${workflowId}/hitl/resume`, decisionData);
  return data;
}

export async function fetchArtifactContent(workflowId, artifactRef) {
  const { data } = await apiClient.get(`${BASE()}/${workflowId}/artifacts`, {
    params: { ref: artifactRef }
  });
  return data;
}
```

### 5.3 Real-Time SSE Stream Hook (`useOrchestratorEvents.js`)
```javascript
import { useEffect, useState } from 'react';
import { getDynamicWorkflowApiUrl } from '../../config/config';

export function useOrchestratorEvents(workflowId) {
  const [events, setEvents] = useState([]);
  const [currentState, setCurrentState] = useState(null);

  useEffect(() => {
    if (!workflowId) return;

    const eventSource = new EventSource(
      `${getDynamicWorkflowApiUrl()}/api/dynamic-workflow/${workflowId}/events`
    );

    eventSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data);
      setEvents((prev) => [...prev, parsed]);

      if (parsed.event === 'plan_updated') {
        setCurrentState((prev) => ({ ...prev, plan: parsed.new_steps }));
      } else if (parsed.event === 'interrupt_requested') {
        setCurrentState((prev) => ({ ...prev, pendingApproval: parsed }));
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Stream Error:', err);
      eventSource.close();
    };

    return () => eventSource.close();
  }, [workflowId]);

  return { events, currentState };
}
```

### 5.4 Routes Registration (`src/routes/AppRoutes.jsx`)
Appends new routes cleanly into the existing router array without modifying existing pages:
```jsx
// AppRoutes.jsx
<Route path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR} element={<DynamicWorkflowOrchestratorPage />} />
<Route path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL} element={<DynamicWorkflowOrchestratorExecution />} />
```

---

## 6. Environment Configurations (`.env.sample`)

```ini
# ==============================================================================
# Azure OpenAI Settings (Required for Intent Classification & Dynamic Planning)
# ==============================================================================
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# ==============================================================================
# Orchestrator Core Tuning
# ==============================================================================
DWF_ENVIRONMENT=development
DWF_PLANNING_TIMEOUT_MS=30000
DWF_MAX_AGENTS_PER_WORKFLOW=10
DWF_MAX_REPLAN_ITERATIONS=6
DWF_IDEMPOTENCY_TTL_SECONDS=86400

# ==============================================================================
# MongoDB (Business Workflow Persistence & Virtual Filesystem GridFS)
# ==============================================================================
DWF_MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0
DWF_MONGODB_DATABASE=dwf_orchestrator

# ==============================================================================
# Checkpointing Backend Choice (Postgres or Redis for LangGraph State)
# ==============================================================================
DWF_CHECKPOINT_BACKEND=postgres # postgres | redis

# Postgres Connection Parameters
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=dwf_db
DWF_POSTGRES_URI=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Redis Connection Parameters
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
DWF_REDIS_URI=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# ==============================================================================
# Security & Tokens
# ==============================================================================
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_SECONDS=3600
JWT_REFRESH_TOKEN_EXPIRY_SECONDS=86400

# ==============================================================================
# Agent Registry Configuration
# ==============================================================================
DWF_AGENTS_REGISTRY_PATH=registry/agents.json

# ==============================================================================
# React Frontend Environment Variables (.env)
# ==============================================================================
REACT_APP_DYNAMIC_WORKFLOW_API_URL=http://localhost:7072
REACT_APP_ENVIRONMENT=development
```

---

## 7. Implementation Sequence for Engineering Team

1. **Backend Scaffolding:** Create `backend/` directory structure, `requirements.txt`, and `.env.sample`.
2. **Pydantic Models:** Implement `models/envelope.py`, `models/workflow.py`, and `models/hitl.py`.
3. **Agent Registry & HTTP Invoker:** Implement `services/agent_registry.py` and `services/agent_client.py`.
4. **Deep Agents Graph & Planner:** Build `domain/orchestrator_graph.py`, `domain/planning.py`, and `domain/agent_tools.py`.
5. **Virtual Filesystem:** Implement `services/filesystem_store.py` for payload offloading (>2KB).
6. **Dual Controllers:** Implement `api.py` and mirror in `functions/*`.
7. **Frontend API & Hook Layer:** Build `OrchestratorApi.js` and `useOrchestratorEvents.js` in `Forge-X-Web`.
8. **Frontend Components:** Implement `DynamicWorkflowOrchestratorPage.jsx`, `WorkflowGraph/`, `HITLPanel/`, and `ArtifactViewer/`.
9. **Routing Registration:** Append routes to `AppRoutes.jsx` and `routesPath.js`.
10. **E2E Validation:** Test complete query execution flow locally via FastAPI and verify UI reactivity.
