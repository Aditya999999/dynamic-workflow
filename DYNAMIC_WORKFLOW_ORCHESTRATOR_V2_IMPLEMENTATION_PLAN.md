# Dynamic Workflow Orchestrator V2 — Implementation Plan
### Deep Agents–Based Multi-Agent Orchestration for BA / PO / Architect / Dev / QE Agents

**Status:** Fresh build (greenfield) — replaces prior static-DAG orchestrator design
**Audience:** Coding agent / engineering team implementing from scratch
**Owner context:** Existing agent fleet already deployed as independent Azure Function Apps; this document defines the orchestrator that sits in front of them.

---

## 1. Background & Why This Exists

We have **5 independent, already-deployed agent microservices**, each an Azure Function App with its own REST contract:

| Agent | Function App | Status |
|---|---|---|
| Business Analyst (BA) | `forgex-dev-fun-ba` | Verified, invocable |
| Architect | `arch-rest-dev` | Mock (contract unverified) |
| Development (Dev) | `forgex-dev-fun-devagent` | Mock |
| Product Owner (PO) | `forgex-dev-fun-po` | Mock |
| QE | *(pending registration)* | Mock |

Each agent exposes **10–15 endpoints**, not one — task endpoints (create BRD, generate user stories, render architecture diagrams, etc.) plus lifecycle endpoints (health, session, conversation store/get/delete, synopsis, async job status/cancel) plus admin endpoints (skill upload/download/update, JIRA/Azure DevOps connection toggles).

### The problem with the original design
The first iteration of this system (`dynamic_workflow` repo) used a **precomputed, static DAG**: an LLM intent classifier + capability-matching agent selector produced a full node/edge graph up front (topological sort, cycle detection), persisted to MongoDB, then executed node-by-node. This is fully deterministic and auditable, but cannot handle:
- An agent that, mid-task, determines it needs another agent's output before it can finish (e.g., Architect needs a clarified NFR from BA).
- Human-in-the-loop approval gates that can **edit** an artifact and change what happens next.
- Artifacts too large to keep in LLM context across every hand-off (BRDs, OpenAPI specs, generated code, Mermaid diagrams).

### The new approach
Rebuild the orchestrator core on **LangChain's Deep Agents** framework (LangGraph-based), which natively provides:
- A **planning loop** that can dynamically decide the next agent to invoke based on the last agent's result (not a fixed pre-computed graph).
- **Human-in-the-loop** via `interrupt()` / `HumanInTheLoopMiddleware` with approve / edit / reject / respond, backed by a checkpointer for pause-resume.
- A **virtual filesystem** for offloading large artifacts out of LLM context, referenced by path.
- A **skills/tool-manifest layer** that can be refreshed when an agent's own skill blob changes.

This plan is a **fresh, greenfield build**. Do not attempt to reuse or patch the old static-DAG orchestrator code — build the new domain/service layer from scratch per the architecture below, while keeping the *existing* 5 agent Function Apps and the *existing* Forge-X-Web frontend shell completely untouched. Only new code is added; nothing existing is broken.

---

## 2. High-Level Architecture

```
                        ┌─────────────────────────────┐
                        │   Forge-X-Web Frontend       │
                        │  (new DynamicWorkflow         │
                        │   Orchestrator module)        │
                        └───────────────┬───────────────┘
                                        │ Bearer JWT (existing axiosClient.js)
                                        ▼
        ┌───────────────────────────────────────────────────────┐
        │           Orchestrator Backend (dual-controller)         │
        │  ┌───────────────┐        ┌───────────────────────┐    │
        │  │ api.py         │        │ function_app.py         │    │
        │  │ (FastAPI,      │        │ (Azure Functions,       │    │
        │  │  local dev)    │        │  production deploy)     │    │
        │  └───────┬───────┘        └───────────┬───────────┘    │
        │          └────────────┬────────────────┘                │
        │                       ▼                                 │
        │        domain/ (Deep Agents orchestrator core)          │
        │   - planning loop (LangGraph)                           │
        │   - agent tool wrappers (per agents.json)                │
        │   - HITL interrupt gates                                 │
        │   - virtual filesystem manager                           │
        │   - skill/tool-manifest sync                             │
        │                       │                                 │
        │        services/ (shared infra clients)                 │
        │   - agent_client.py (generic HTTP invoker)                │
        │   - checkpointer.py (Postgres/Redis — LangGraph state)   │
        │   - mongo_client.py (workflow business state)            │
        │   - filesystem_store.py (artifact blob/Mongo GridFS)     │
        └───────────────┬────────────────┬─────────────────────────┘
                        │                │
        ┌───────────────▼───┐  ┌────────▼────────┐  ┌──────────────┐
        │  BA Agent           │  │ Architect Agent  │  │ Dev / PO / QE│
        │ (Azure Function App)│  │ (Azure Function) │  │ (Azure Fn)   │
        └─────────────────────┘  └──────────────────┘  └──────────────┘
```

**Key principle:** `api.py` (FastAPI, local) and `function_app.py` (Azure Functions, prod) are **thin controllers only**. All business logic lives in `domain/` and `services/`, imported identically by both. This is non-negotiable — it is the only way the two deployment targets stay behaviorally identical.

---

## 3. Repository Structure (Backend)

```
dynamic-workflow-orchestrator/
├── api.py                        # FastAPI app — local dev entrypoint
├── function_app.py               # Azure Functions app — prod entrypoint
├── host.json                     # Azure Functions host config
├── local.settings.json.sample    # Azure Functions local settings template
├── pyproject.toml / requirements.txt
│
├── functions/                    # Azure Function bindings — one file per route,
│   │                              # mirrors api.py routes 1:1, thin pass-through only
│   ├── plan_workflow.py
│   ├── execute_workflow.py
│   ├── get_workflow.py
│   ├── list_agents.py
│   ├── cancel_workflow.py
│   ├── hitl_resume.py
│   ├── get_artifact.py
│   └── health.py
│
├── config/
│   ├── settings.py               # single source of truth, reads env for both controllers
│   └── env.sample                # see Section 8
│
├── domain/                       # Orchestrator core — controller-agnostic
│   ├── orchestrator_graph.py     # Deep Agents / LangGraph graph construction & invoke
│   ├── planning.py               # planning loop config, system prompt, replanning rules
│   ├── agent_tools.py            # codegen/registration of per-agent LangChain tools
│   ├── response_envelope.py      # normalizes each agent's raw response → standard envelope
│   ├── hitl_gates.py             # interrupt_on config, approval routing rules
│   ├── skill_sync.py             # agents.json capability diff → tool manifest refresh
│   └── workflow_state.py         # LangGraph state schema (messages, plan, artifacts refs)
│
├── models/                       # Pydantic — shared request/response schemas
│   ├── agent_contracts.py        # per-agent request/response models (BA, Architect, Dev, PO, QE)
│   ├── envelope.py                # StandardAgentResponse (status/result/next_action_hint/confidence)
│   ├── workflow.py                # WorkflowPlanRequest, WorkflowDocument, NodeResult
│   └── hitl.py                    # ApprovalRequest, ApprovalDecision
│
├── services/                     # Shared infra clients
│   ├── agent_client.py           # generic async HTTP invoker, reads agents.json registry
│   ├── agent_registry.py         # loads/validates agents.json, tiering (task/lifecycle/admin)
│   ├── checkpointer.py           # LangGraph checkpointer factory (Postgres or Redis)
│   ├── mongo_client.py           # business workflow persistence (dwf_workflows, dwf_events)
│   ├── filesystem_store.py       # virtual FS abstraction — backed by Mongo GridFS or Blob Storage
│   ├── auth.py                   # JWT verify/decode — shared by both controllers
│   ├── sse.py                    # SSE event formatting/streaming helper
│   └── logging.py
│
├── registry/
│   └── agents.json               # extended agent registry — see Section 6
│
├── tests/
│   ├── unit/
│   │   ├── test_agent_tools.py
│   │   ├── test_response_envelope.py
│   │   ├── test_orchestrator_graph.py
│   │   ├── test_hitl_gates.py
│   │   └── test_filesystem_store.py
│   └── integration/
│       └── test_full_workflow_e2e.py   # mocked agent responses, real graph execution
│
└── README.md
```

### Controller parity rule
For every capability, there must be exactly one `domain/` or `services/` function, called from:
- one FastAPI route in `api.py`
- one Azure Function binding file in `functions/`

Neither controller file may contain conditionals, transformations, or business rules — only: auth check → parse into a `models/` schema → call domain function → serialize response / stream SSE.

---

## 4. Orchestrator Core Design (Deep Agents / LangGraph)

### 4.1 Planning loop, not static DAG
The orchestrator is a **planning agent** (LangGraph graph) whose tools are the 5 agent invokers (Section 6). Its system prompt instructs it to:
1. Decompose the user's NLQ into an initial plan (still produced up front, for auditability — see 4.2).
2. Execute agent calls in planned order **by default**.
3. After every agent call, inspect the `StandardAgentResponse.next_action_hint` and `status` fields (Section 5) and **replan** if the result signals `needs_input`, `blocked`, or a dependency on another agent not in the original plan.
4. Never call an agent tool that requires interrupt approval without first pausing for that approval.

### 4.2 Hybrid determinism (recommended default)
Per the earlier POC recommendation — **do not go fully nondeterministic on day one**:
- Keep an initial deterministic planning step (equivalent to the old `intent_classifier.py` + `agent_selector.py` + `workflow_sequencer.py`) that proposes a plan (ordered list of agent invocations) — implement this in `domain/planning.py` as the graph's entry node.
- The Deep Agents planning loop **executes** this plan but is explicitly permitted to insert additional agent calls / re-invoke a prior agent only when an agent's response signals it via `next_action_hint`.
- Log every deviation from the original plan as a `plan_updated` event (Section 9) for auditability.

### 4.3 Dynamic re-invocation contract
An agent is allowed to cause the orchestrator to call another agent (or itself) again **only through its response envelope**, never through free-text the LLM has to infer. See Section 5.

### 4.4 State schema (`domain/workflow_state.py`)
LangGraph state for each workflow run:
```python
class OrchestratorState(TypedDict):
    workflow_id: str
    workspace_id: str
    user_id: str
    user_query: str
    messages: list              # LLM planning conversation
    plan: list[PlannedStep]     # initial deterministic plan
    executed_steps: list[ExecutedStep]
    artifacts: dict[str, ArtifactRef]   # path -> {agent, type, summary, size}
    pending_approval: ApprovalRequest | None
    status: Literal["planned", "executing", "awaiting_approval", "completed", "failed", "cancelled"]
```

---

## 5. Standard Agent Response Envelope

Every agent's raw response is heterogeneous (see Section 6.2 for real payload shapes). The orchestrator never reasons over raw agent payloads directly — `domain/response_envelope.py` normalizes every response into:

```json
{
  "status": "completed | needs_input | blocked | error",
  "result": { "...": "agent-specific payload, unchanged" },
  "artifact_ref": "/workspace/{workflow_id}/{agent}/{artifact_name}.md",
  "artifact_summary": "one or two sentence summary for LLM context",
  "next_action_hint": "handoff_to_architect | retry_self | request_human | request_agent:po | none",
  "confidence": 0.0
}
```

- `result` is only kept in full if small (< ~2KB); otherwise it is written to the virtual filesystem and only `artifact_ref` + `artifact_summary` are returned to the planning loop's context.
- `next_action_hint` is the **only** channel through which an agent can cause dynamic re-invocation. Build a mapping function per agent (since raw payloads differ) that derives this from each agent's actual response fields (e.g., BA agent's `missing_field`, Architect's `validation_errors`, etc.) — implement one adapter function per agent in `response_envelope.py`.

---

## 6. Agent Registry (`registry/agents.json`) — Extended Schema

Extend the existing single-endpoint-per-agent schema to a **tiered, multi-endpoint** model. Endpoints are tagged by `category`, and only `task`-category endpoints become LLM-callable tools.

### 6.1 Schema
```json
{
  "agent_id": "business-analyst",
  "display_name": "Business Analyst Agent",
  "contract_version": "1.0.0",
  "purpose": "Generate and manage Business Requirements Documents, classify BA intents, execute BRD creation, human feedback incorporation, JIRA queries, and knowledge base queries",
  "capabilities": ["brd_generation", "requirements_analysis", "feedback_incorporation", "jira_query", "kb_query"],
  "status": "active",
  "contract_status": "verified",
  "invocation_enabled": true,
  "environment_bindings": {
    "local": { "base_url": "http://localhost:7071/api", "auth_scheme": "none" },
    "development": { "base_url": "https://forgex-dev-fun-ba-e8cqh7f2bkb6c0hh.eastus2-01.azurewebsites.net/api", "auth_scheme": "bearer_jwt" }
  },
  "endpoints": {
    "task": [
      {
        "name": "create_brd",
        "route": "dynamic-workflow/ba-task",
        "method": "POST",
        "category": "task",
        "exposed_as_tool": true,
        "request_schema": "models.agent_contracts.BATaskRequest",
        "response_schema": "models.agent_contracts.BATaskResponse",
        "timeout_ms": 300000
      },
      {
        "name": "get_synopsis",
        "route": "get-synopsis",
        "method": "POST",
        "category": "task",
        "exposed_as_tool": true
      },
      {
        "name": "edit_synopsis",
        "route": "edit-synopsis",
        "method": "POST",
        "category": "task",
        "exposed_as_tool": true
      },
      {
        "name": "jira_agent",
        "route": "jira-agent",
        "method": "POST",
        "category": "task",
        "exposed_as_tool": true
      }
    ],
    "lifecycle": [
      { "name": "health", "route": "health", "method": "GET", "category": "lifecycle" },
      { "name": "create_session", "route": "create-session", "method": "POST", "category": "lifecycle" },
      { "name": "store_conversation", "route": "store-conversation", "method": "POST", "category": "lifecycle" },
      { "name": "get_conversation", "route": "get-conversation", "method": "GET", "category": "lifecycle" },
      { "name": "delete_conversation", "route": "delete-conversation", "method": "POST", "category": "lifecycle" },
      { "name": "send_message_status", "route": "send-message-status", "method": "GET", "category": "lifecycle" },
      { "name": "cancel_job", "route": "cancel-job", "method": "POST", "category": "lifecycle" }
    ],
    "admin": [
      { "name": "upload_skill_blob", "route": "upload-skill-blob", "method": "POST", "category": "admin" },
      { "name": "download_skill_blob", "route": "download-skill-blob", "method": "POST", "category": "admin" },
      { "name": "update_skill", "route": "update-skill", "method": "POST", "category": "admin" },
      { "name": "test_jira_connection", "route": "test-jira-connection", "method": "POST", "category": "admin" },
      { "name": "toggle_jira_connection", "route": "toggle-jira-connection", "method": "POST", "category": "admin" }
    ]
  },
  "timeout_policy": { "default_ms": 300000, "max_ms": 900000 },
  "retry_policy": { "max_retries": 1, "backoff_base_ms": 2000 },
  "requires_human_approval": true,
  "ownership": "ba-team",
  "tags": ["sdlc", "requirements", "documentation"]
}
```

Repeat this shape for `architect`, `dev`, `product-owner`, `qe` — populate `endpoints` from the actual API sheets already documented by the team (Excel tabs: Devagent, BaAgent, PoAgent, Architect Agent, KB Agent). QE's registry entry should be added even though its Function App URL is still pending — mark `invocation_enabled: false` and `contract_status: "pending"` until verified.

### 6.2 Runtime call tiers
| Category | Who calls it | When |
|---|---|---|
| `task` | Orchestrator planning loop (LLM-selected tool) | Per query-driven decision |
| `lifecycle` | Orchestrator runtime wrapper (automatic, never LLM-decided) | `health` pre-flight before first call; `create_session` once per workflow; `store/get-conversation` before/after every agent turn; `send-message-status`/`cancel-job` for async polling |
| `admin` | Event-triggered (skill upload UI, connection setup UI) | Not part of query-time routing at all |

`services/agent_client.py` implements the lifecycle wrapper (session bootstrap → invoke task → persist conversation → poll if async) around every task invocation automatically; `domain/agent_tools.py` only ever generates LangChain tools for `task`-category endpoints.

---

## 7. Human-in-the-Loop (HITL)

### 7.1 Mechanism
Use LangGraph's `interrupt()` primitive via `HumanInTheLoopMiddleware`, configured in `domain/hitl_gates.py`:

```python
interrupt_on = {
    "invoke_ba_create_brd": {"allowed_decisions": ["approve", "edit", "reject"]},
    "invoke_architect_generate_design": True,
    # tools not listed here execute without a gate
}
```

- Requires a checkpointer (`services/checkpointer.py`, Postgres or Redis per `.env`) + `thread_id` = `workflow_id`.
- On interrupt, orchestrator run pauses; state is durably checkpointed; the API/Function returns a `pending_approval` status with the artifact reference for review.
- Resume via `Command(resume={"decisions": [...]})`. All code before the `interrupt()` call re-executes on resume — ensure any side-effecting calls in `agent_tools.py` are idempotent (use upsert patterns in Mongo persistence, never blind insert).

### 7.2 Which hand-offs are gated by default
Configurable per workflow, but recommended defaults for V1:
- BA → Architect handoff (BRD approval before design starts)
- Architect → Dev handoff (design approval before code generation)
- Any agent's `next_action_hint == "request_human"` (agent-signaled, always gated regardless of tool config)

### 7.3 API surface
- `POST /api/dynamic-workflow/{workflow_id}/hitl/resume` — body: `{decision: "approve"|"edit"|"reject", edited_content?: str, feedback?: str}`
- Emits `hitl_resolved` SSE event on completion (Section 9).

---

## 8. Filesystem-Backed Artifact Storage

### 8.1 Purpose
Prevent large artifacts (BRDs, OpenAPI specs, generated code, Mermaid diagrams) from ever entering the LLM planning context in full.

### 8.2 Implementation (`services/filesystem_store.py`)
- Backing store: MongoDB GridFS (co-located with existing `dwf_workflows`/`dwf_events` collections) for V1 — swap to Azure Blob Storage later if needed without changing the interface.
- Path convention: `/workspace/{workflow_id}/{agent_id}/{artifact_name}.{ext}`
- Interface:
  ```python
  async def write_artifact(workflow_id, agent_id, name, content, content_type) -> ArtifactRef
  async def read_artifact(path) -> str
  async def read_artifact_section(path, start, end) -> str   # for partial injection
  ```
- Every `agent_tools.py` wrapper checks response size post-envelope-normalization; anything over a configurable threshold (default 2KB) is written to the filesystem and only `artifact_ref` + `artifact_summary` re-enters LLM context.
- When a downstream agent needs the artifact, the orchestrator either (a) passes the path and lets that agent's tool wrapper fetch + inject only the relevant section, or (b) calls `read_artifact_section` itself before constructing the next tool call payload.

### 8.3 Persistence relationship to MongoDB workflow doc
`dwf_workflows.nodes[].invocation_metadata.result` should store `{artifact_ref, artifact_summary}` only — not full content — going forward. Full content lives exclusively in the filesystem store.

---

## 9. Skill Sync (Dynamic Capability Awareness)

Two distinct concerns — do not conflate them:

1. **Agent-side behavior change** (via each agent's own `/upload-skill-blob`): fully opaque to the orchestrator. No orchestrator action needed — the agent just behaves differently on its next task call.
2. **Orchestrator-side routing awareness** (`domain/skill_sync.py`): when an agent's `capabilities` array in `agents.json` changes (version bump), the orchestrator's tool **descriptions** (docstrings shown to the planning LLM) must be regenerated so routing decisions reflect new/removed capabilities. Implement as:
   - `skill_sync.py` diffs `agents.json` on load (checksum or version field) against last-registered tool manifest.
   - On change, regenerate `agent_tools.py` tool objects for that agent only (title/description updated), without requiring a full orchestrator redeploy — reload at graph-construction time per request, or on a TTL cache.

---

## 10. SSE Event Contract (Frontend Sync)

Extend the existing event stream with new event types required for the dynamic model:

| Event | Payload | Purpose |
|---|---|---|
| `node_started` | `{node_id, agent_id}` | existing, unchanged |
| `node_completed` | `{node_id, agent_id, status}` | existing, unchanged |
| `plan_updated` | `{workflow_id, new_steps, reason}` | **new** — plan changed mid-execution |
| `interrupt_requested` | `{workflow_id, tool_name, artifact_ref, message}` | **new** — drives HITL approval UI |
| `hitl_resolved` | `{workflow_id, decision}` | **new** |
| `artifact_written` | `{workflow_id, agent_id, artifact_ref, artifact_summary, size_bytes}` | **new** — drives artifact viewer |
| `workflow_completed` / `workflow_failed` | existing | unchanged |

---

## 11. API Surface (both controllers, identical contract)

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/dynamic-workflow/plan` | Produce initial deterministic plan from NLQ |
| POST | `/api/dynamic-workflow/{workflow_id}/execute` | Start/resume execution (Deep Agents graph run) |
| GET | `/api/dynamic-workflow/{workflow_id}` | Retrieve workflow doc |
| GET | `/api/dynamic-workflow/{workflow_id}/events` | SSE stream (Section 10 event types) |
| GET | `/api/dynamic-workflow/{workflow_id}/artifacts/{artifact_id}` | Fetch artifact content by ref |
| POST | `/api/dynamic-workflow/{workflow_id}/hitl/resume` | Resume from interrupt |
| POST | `/api/dynamic-workflow/{workflow_id}/cancel` | Cancel workflow |
| GET | `/api/dynamic-workflow/agents` | List registered agents (from agents.json) |
| GET | `/api/dynamic-workflow/health` | Health check |

Azure Functions bindings in `functions/` mirror this table exactly, one file per row.

---

## 12. Frontend Plan (Forge-X-Web integration)

### 12.1 Placement
New module, sibling to the existing `DynamicWorkflow/` component — do not modify existing code:
```
src/components/DynamicWorkflowOrchestrator/
├── OrchestratorApi.js            # mirrors dynamicWorkflowApi.js, reuses apiClient (axiosClient.js)
├── useOrchestratorEvents.js      # SSE hook; branches on new event types (Section 10)
├── DynamicWorkflowOrchestratorPage.jsx
├── PlanSummary/                   # reuse pattern from existing PlanSummary.jsx if schema-compatible
├── QueryInput/                    # reuse pattern from existing QueryInput.jsx
├── WorkflowGraph/                 # reuse XY Flow graph rendering; add plan_updated re-render support
│   ├── WorkflowGraph.jsx
│   └── AgentNode.jsx
├── HITLPanel/
│   ├── PendingApprovals.jsx       # list of open interrupt_requested events
│   └── ApprovalCard.jsx           # approve / edit / reject UI, calls hitl/resume
├── ArtifactViewer/
│   ├── ArtifactBrowser.jsx        # tree/list view over /workspace/{workflow_id}/*
│   └── ArtifactPreview.jsx        # type-aware render: markdown (BRD), mermaid (diagrams), code
└── SkillManager/
    └── SkillUploadPanel.jsx       # wraps each agent's upload-skill-blob; triggers skill_sync refresh
```

### 12.2 Reused infrastructure (do not rebuild)
- `axiosClient.js` — Bearer token attach + 401 handling + session extension, used as-is.
- `sessionManager.js` / `authTokenManager.js` — unchanged.
- `AppRoutes.jsx` pattern — add new route constants (e.g. `DYNAMIC_WORKFLOW_ORCHESTRATOR`, `DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL`) following the exact same `<Route path={routesPath.X} element={<Y/>}/>` convention already used for `DYNAMIC_WORKFLOW` / `DYNAMIC_WORKFLOW_DETAIL`.

### 12.3 Route additions (append to existing `AppRoutes.jsx`, do not restructure)
```jsx
<Route path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR} element={<DynamicWorkflowOrchestratorPage />} />
<Route path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL} element={<DynamicWorkflowOrchestratorExecution />} />
```

---

## 13. Environment Configuration

### 13.1 `.env.sample` (backend)
```ini
# --- Azure OpenAI (required for planning loop) ---
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# --- Orchestrator Settings ---
DWF_ENVIRONMENT=development
DWF_PLANNING_TIMEOUT_MS=30000
DWF_MAX_AGENTS_PER_WORKFLOW=10
DWF_MAX_QUERY_LENGTH=10000
DWF_IDEMPOTENCY_TTL_SECONDS=86400
DWF_MAX_REPLAN_ITERATIONS=6          # guardrail against runaway dynamic re-invocation

# --- MongoDB (business workflow persistence + artifact GridFS) ---
DWF_MONGODB_URI=
DWF_MONGODB_DATABASE=dwf_orchestrator

# --- Checkpointer (LangGraph state — HITL pause/resume, plan state) ---
DWF_CHECKPOINT_BACKEND=postgres      # postgres | redis
DWF_POSTGRES_URI=
DWF_REDIS_URI=

# --- SSE / streaming tuning ---
DWF_SSE_HEARTBEAT_SECONDS=30
DWF_SSE_POLL_INTERVAL_MS=750
DWF_SSE_MAX_OPEN_SECONDS=240
DWF_SSE_RETENTION_HOURS=24

# --- JWT ---
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_SECONDS=3600
JWT_REFRESH_TOKEN_EXPIRY_SECONDS=86400

# --- Agent Registry ---
DWF_AGENTS_REGISTRY_PATH=registry/agents.json
```

### 13.2 Azure Functions specific
`local.settings.json.sample` mirrors the same keys under `Values`, plus:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

---

## 14. Dependencies

```
# Core
fastapi
uvicorn
azure-functions

# Deep Agents / LangGraph
langchain
langgraph
langchain-deepagents
langchain-openai         # or langchain-azure-openai for AOAI
langchain-mongodb        # checkpointer/store option
langgraph-checkpoint-postgres   # if DWF_CHECKPOINT_BACKEND=postgres
langgraph-checkpoint-redis      # if DWF_CHECKPOINT_BACKEND=redis

# Infra
motor / pymongo
httpx
pydantic
python-jose               # JWT
redis                     # if used

# Testing
pytest
pytest-asyncio
respx                     # mock httpx calls to agent Function Apps
```

---

## 15. Build Order (recommended sequence for the coding agent)

1. **Scaffolding**: repo structure per Section 3, `.env.sample`, `agents.json` (BA + Architect only for now, full schema).
2. **`models/`**: `envelope.py`, `agent_contracts.py` (BA + Architect request/response), `workflow.py`.
3. **`services/agent_registry.py`**: load + validate `agents.json`, expose tiered endpoint lookup.
4. **`services/agent_client.py`**: generic invoker (health check → session → task call → conversation persist), used by tool wrappers.
5. **`domain/response_envelope.py`**: BA + Architect adapters → `StandardAgentResponse`.
6. **`domain/agent_tools.py`**: generate LangChain tools for BA + Architect `task` endpoints only.
7. **`domain/workflow_state.py`** + **`domain/orchestrator_graph.py`**: minimal planning loop, no HITL yet — straight sequential BA → Architect call, verify end-to-end.
8. **`services/filesystem_store.py`**: wire artifact offload for BA's BRD output; verify Architect invocation receives `artifact_ref` correctly.
9. **`services/checkpointer.py`** + **`domain/hitl_gates.py`**: add one interrupt gate (BA → Architect), verify pause/resume via a manual `hitl/resume` call.
10. **Controllers**: `api.py` (FastAPI) routes for `plan`, `execute`, `hitl/resume`, `events` (SSE) — get local dev loop fully working.
11. **`function_app.py` + `functions/`**: mirror the same routes as Azure Function bindings, confirm parity against `api.py` using the same test suite.
12. **Frontend scaffold**: `DynamicWorkflowOrchestrator/` module, wired to the 2-agent backend, HITL approval UI functional end-to-end.
13. **Extend to Dev, PO, QE**: repeat steps 2–6 per agent once BA↔Architect loop is validated.
14. **`domain/skill_sync.py`**: wire capability-change → tool manifest refresh.
15. **Guardrails & hardening**: `DWF_MAX_REPLAN_ITERATIONS`, retry/backoff per `agents.json`, idempotency keys, structured logging, load test SSE under concurrent workflows.

---

## 16. Explicit Non-Goals for V1

- Do **not** migrate the existing static-DAG `dynamic_workflow` repo or its frontend `DynamicWorkflow/` component — this is a new, additive module.
- Do **not** expose `lifecycle` or `admin` category endpoints as LLM-selectable tools under any circumstances.
- Do **not** allow unlimited replanning — `DWF_MAX_REPLAN_ITERATIONS` must hard-stop runaway loops.
- Do **not** store full artifact content in `dwf_workflows` Mongo documents going forward — filesystem store + reference only.
- QE agent integration is deferred until its Function App is registered and contract-verified (`contract_status: "pending"` in registry blocks tool generation).

---

## 17. Open Items for the Team (flag, don't block on)

- Confirm checkpoint backend choice (Postgres vs Redis) — either works; pick based on existing infra ownership.
- Architect / Dev / PO agents are currently mock/contract-unverified — `agent_tools.py` generation for these should be gated behind `contract_status: "verified"` in `agents.json` until confirmed live.
- Decide artifact size threshold for filesystem offload (default 2KB proposed; may need tuning per artifact type — Mermaid diagrams and code files may warrant a lower threshold than prose).
