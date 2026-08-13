# Deep Agents Dynamic Workflow Orchestrator V7 — Master Implementation Specification

**Document Version:** 7.0 (Final Greenfield + Exact Screenshot Repository Layout + Office Portable)  
**Implementation Mode:** Fresh local development with direct portability to the office environment  
**Primary Agent Framework:** **Deep Agents** (`langchain-deepagents`)  
**Backend:** Python + FastAPI (Local) & Azure Functions v2 (Office Deploy)  
**Frontend Repository Target:** **`frontend/Forge-X-Web/`**  
**Persistence:** MongoDB (`dwf_orchestrator`)  
**Artifact Storage:** MongoDB GridFS abstraction (Future Azure Blob Storage compatible)  
**Workflow Visualization:** `@xyflow/react`  
**Target Deployment Model:** Local development first using mocks/docker-compose; later deployed into office environment via `.env` substitution and repository merge without rewriting source code.

---

# 1. Critical Clarification & Portability Principle

This project is developed from scratch in the current environment, but it is **not intended to become a separate standalone frontend or backend architecture**.

The final code strictly reproduces the **`src/dwf/`** backend modular structure and **`frontend/Forge-X-Web/`** structure shown in the codebase screenshot (`2_2.jpeg`):

```text
dynamic_workflow/
├── backend/
│   ├── function_app.py
│   ├── app.py
│   ├── host.json
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.sample
│   │
│   ├── src/
│   │   └── dwf/                 # EXACT DOMAIN LOGIC MODULE FROM SCREENSHOT
│   │       ├── api.py
│   │       ├── config/
│   │       ├── domain/
│   │       ├── persistence/
│   │       ├── registry/
│   │       ├── invocation/
│   │       ├── policy/
│   │       ├── streaming/
│   │       └── errors/
│   │
│   ├── functions/               # THIN AZURE FUNCTION HANDLERS
│   └── tests/
│
└── frontend/
    └── Forge-X-Web/             # TARGET OFFICE FRONTEND REPOSITORY
```

---

# 2. Main Objective

Build a dynamic multi-agent workflow orchestrator using **Deep Agents**.

The system sits between:

```text
Forge-X-Web React Frontend
            |
            v
Dynamic Workflow Orchestrator (Deep Agents Runtime inside src/dwf)
            |
            +---- Business Analyst (BA) Agent
            +---- Architect Agent
            +---- Developer Agent
            +---- Product Owner (PO) Agent
            +---- Quality Engineering (QE) Agent
```

The orchestrator must support:
* Natural-language workflow requests (NLQ).
* Initial deterministic/dynamic plan generation.
* Dynamic runtime replanning (triggered by agent output `next_action` signals).
* Capability-based agent task selection.
* Structured task invocation with lifecycle auto-wrapping (health, session creation, conversation logging).
* Large payload offloading to virtual filesystem (>2KB stored in GridFS, returning `artifact_ref`).
* Human-in-the-Loop (HITL) approval gates with approve/edit/reject actions.
* Workflow persistence & execution event streaming (SSE replay & reconnect).
* `@xyflow/react` visual graph synchronization.
* Retries, cancellation, idempotency, and auditability.

---

# 3. Architecture Ownership & Boundaries

## 3.1 Application Layer (`src/dwf`) Owns
- Workflow ID, workspace ID, user context.
- Workflow execution status & graph schema (nodes/edges).
- Plan versioning & step tracking.
- Agent registry (`registry/agents.json`), capabilities, and access policy (`policy/`).
- Retries, replan limits, cycle limits, and duration timeouts.
- Artifact metadata and storage grid (`persistence/`).
- Audit event logging (`streaming/`).
- Cancellation, API contracts, JWT authentication, and frontend SSE stream.

## 3.2 Deep Agents Layer Owns
- Intelligent planning loop and tool selection inside `src/dwf/domain/`.
- Task decomposition and context management.
- Dynamic next-step reasoning based on agent response envelopes.
- Resumable subagent execution via checkpointer state (`Postgres` / `Redis`).

---

# 4. Exact Screenshot Repository Directory Model

The directory model mirrors the snapshot (`2_2.jpeg`) while incorporating the Deep Agents modular architecture:

```text
dynamic_workflow/
│
├── backend/
│   ├── function_app.py                  # Azure Functions v2 entrypoint (thin triggers)
│   ├── app.py                           # FastAPI / gunicorn entrypoint (local dev)
│   ├── host.json                        # Azure host config (10-min timeout)
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.sample                      # Environment variable template
│   │
│   ├── src/
│   │   └── dwf/                         # DOMAIN LOGIC MODULE
│   │       ├── api.py                   # FastAPI app (local dev + tests)
│   │       │
│   │       ├── config/
│   │       │   └── settings.py          # Environment-based configuration
│   │       │
│   │       ├── domain/                  # CORE DEEP AGENTS & PYDANTIC MODELS
│   │       │   ├── models.py            # All canonical Pydantic models
│   │       │   ├── intent_classifier.py # Azure OpenAI LLM-based classification
│   │       │   ├── agent_selector.py   # Capability-based agent matching
│   │       │   ├── workflow_sequencer.py# DAG builder, cycle detection
│   │       │   └── workflow_manager.py  # Planning + execution coordinator (Deep Agents)
│   │       │
│   │       ├── persistence/             # DATABASE & STORAGE CLIENTS
│   │       │   ├── mongo.py             # Async MongoDB client (Motor)
│   │       │   ├── workflow_store.py    # Workflow CRUD with optimistic concurrency
│   │       │   └── filesystem_store.py  # GridFS virtual filesystem manager (>2KB)
│   │       │
│   │       ├── registry/                # AGENT REGISTRY & CAPABILITIES
│   │       │   ├── agents.json          # 5-agent bootstrap manifest
│   │       │   ├── store.py             # In-memory registry with JSON bootstrap
│   │       │   └── service.py           # Lookup, resolution, capability search
│   │       │
│   │       ├── invocation/              # PROTOCOL ADAPTERS & EXECUTORS
│   │       │   ├── adapter_base.py      # Protocol-agnostic interface
│   │       │   ├── ba_function_adapter.py# BA-specific request/response translator
│   │       │   ├── rest_adapter.py      # Generic REST adapter
│   │       │   └── router.py            # Adapter dispatch + invocation guard
│   │       │
│   │       ├── policy/                  # GUARDRAILS & LIMITS
│   │       │   ├── enforcer.py          # Deadline and budget checks
│   │       │   └── idempotency.py       # Key-based dedup (Redis)
│   │       │
│   │       ├── streaming/               # REAL-TIME SSE STREAMING
│   │       │   ├── event_emitter.py     # MongoDB-backed SSE event persistence
│   │       │   ├── event_store.py       # Event store & replay reader
│   │       │   └── cancellation.py      # Cooperative cancel state machine
│   │       │
│   │       └── errors/                  # ERROR HANDLING
│   │           └── envelope.py          # Canonical error codes & ErrorResponseEnvelope
│   │
│   ├── functions/                       # THIN AZURE FUNCTION HANDLERS
│   │   ├── plan_workflow.py             # Route: /api/dynamic-workflow/plan
│   │   ├── execute_workflow.py          # Route: /api/dynamic-workflow/{id}/execute
│   │   ├── get_workflow.py              # Route: /api/dynamic-workflow/{id}
│   │   ├── get_node_output.py           # Route: /api/dynamic-workflow/{id}/nodes/{node_id}/output
│   │   ├── get_events.py                # Route: /api/dynamic-workflow/{id}/events (SSE)
│   │   ├── list_agents.py               # Route: /api/dynamic-workflow/agents
│   │   ├── get_agent.py                 # Route: /api/dynamic-workflow/agents/{agent_id}
│   │   ├── cancel_workflow.py           # Route: /api/dynamic-workflow/{id}/cancel
│   │   └── health.py                    # Route: /api/dynamic-workflow/health
│   │
│   └── tests/
│       ├── unit/
│       │   ├── test_domain.py
│       │   ├── test_registry.py
│       │   ├── test_invocation.py
│       │   ├── test_policy.py
│       │   └── test_streaming.py
│       ├── test_api.py                  # API Integration tests
│       └── test_ba.py                   # BA connectivity test
│
└── frontend/
    └── Forge-X-Web/                     # TARGET OFFICE FRONTEND REPOSITORY
        ├── package.json
        ├── .env.example                 # Minimal frontend env containing backend service URL
        └── src/
            ├── config/
            │   ├── axiosClient.js       # Reused JWT Interceptor
            │   ├── config.js            # URL getters
            │   └── environment.js
            ├── routes/
            │   ├── AppRoutes.jsx        # Additive route bindings
            │   └── routesPath.js        # Route constants
            ├── services/
            │   └── orchestratorApi.js   # API client consuming axiosClient
            ├── hooks/
            │   ├── useDynamicWorkflowEvents.js # SSE streaming & event replay hook
            │   └── useWorkflowState.js
            ├── pages/
            │   ├── DynamicWorkflowPage.jsx
            │   └── DynamicWorkflowExecution.jsx
            └── components/
                └── DynamicWorkflow/     # Greenfield UI Module
                    ├── QueryInput/
                    │   └── QueryInput.jsx
                    ├── PlanSummary/
                    │   └── PlanSummary.jsx
                    ├── WorkflowGraph/
                    │   ├── WorkflowGraph.jsx # @xyflow/react canvas auto-layout
                    │   └── AgentNode.jsx
                    ├── HITLPanel/
                    │   ├── PendingApprovals.jsx
                    │   └── ApprovalCard.jsx
                    └── ArtifactViewer/
                        ├── ArtifactBrowser.jsx
                        └── ArtifactPreview.jsx
```

---

# 5. Office Repository Compatibility Rules

1. No absolute local filesystem imports.
2. No imports pointing to hard-coded office-only directories.
3. All domain code must reside under `backend/src/dwf/` so it can be imported cleanly by both `backend/app.py` (FastAPI) and `backend/function_app.py` (Azure Functions).
4. No hard-coded workspace IDs, user IDs, or JWT secrets.
5. All API addresses must be derived from `src/dwf/config/settings.py` (Backend) or `src/config/environment.js` (Frontend).

---

# 6. Environment Configurations

### 6.1 Backend Environment Configuration (`backend/.env.sample`)

```ini
# Azure OpenAI Settings
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Orchestrator Core Tuning
DWF_ENVIRONMENT=development
DWF_PLANNING_TIMEOUT_MS=30000
DWF_MAX_AGENTS_PER_WORKFLOW=10
DWF_MAX_REPLAN_ITERATIONS=6
DWF_IDEMPOTENCY_TTL_SECONDS=86400

# MongoDB Persistence & Virtual Filesystem
DWF_MONGODB_URI=mongodb://localhost:27017
DWF_MONGODB_DATABASE=dwf_orchestrator

# Postgres (LangGraph State Checkpointing)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=dwf_db
DWF_POSTGRES_URI=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Redis (Idempotency & Lock Management)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
DWF_REDIS_URI=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# JWT Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_SECONDS=3600

# Agent Endpoints (mock | live)
AGENT_MODE=mock
BA_AGENT_BASE_URL=http://localhost:7101/api
ARCHITECT_AGENT_BASE_URL=http://localhost:7102/api
DEVELOPER_AGENT_BASE_URL=http://localhost:7103/api
PO_AGENT_BASE_URL=http://localhost:7104/api
QE_AGENT_BASE_URL=http://localhost:7105/api
```

### 6.2 Minimal Frontend Environment Configuration (`frontend/Forge-X-Web/.env.example`)

```ini
REACT_APP_DYNAMIC_WORKFLOW_API_URL=http://localhost:8000
```

---

# 7. Execution Sequence & Implementation Build Order

1. **Phase 1 — Repository Bootstrap:** Set up exact directory layout under `backend/src/dwf/` and `frontend/Forge-X-Web/`.
2. **Phase 2 — Core Models & Errors:** Implement `src/dwf/domain/models.py` and `src/dwf/errors/envelope.py`.
3. **Phase 3 — Persistence Layer:** Build `src/dwf/persistence/mongo.py`, `workflow_store.py`, and `filesystem_store.py`.
4. **Phase 4 — Registry & Invocation:** Implement `src/dwf/registry/` and `src/dwf/invocation/` adapters.
5. **Phase 5 — Deep Agents Domain Engine:** Wire `intent_classifier.py`, `agent_selector.py`, and `workflow_manager.py` using Deep Agents.
6. **Phase 6 — Dual Controllers:** Implement `src/dwf/api.py` (FastAPI) and mirror routes in `backend/functions/` (Azure Functions).
7. **Phase 7 — Frontend Integration:** Implement React pages, `@xyflow/react` graph canvas, and SSE hooks under `frontend/Forge-X-Web/src/components/DynamicWorkflow/`.
