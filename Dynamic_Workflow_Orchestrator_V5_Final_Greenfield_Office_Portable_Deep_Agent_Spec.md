# Dynamic Workflow Orchestrator V5
## Final Greenfield + Office-Repository-Compatible Deep Agent Implementation Specification

**Document version:** 5.0  
**Implementation mode:** Fresh local development with direct portability to the office environment  
**Primary agent framework:** **Deep Agents**  
**Backend:** Python + FastAPI  
**Frontend:** Existing target repository structure **`Forge-X-Web`**  
**Persistence:** MongoDB  
**Artifact storage:** MongoDB GridFS abstraction, future Azure Blob-compatible  
**Workflow visualization:** `@xyflow/react`  
**Target deployment model:** Local development first; later deploy/use in the office environment with the same repository structure and environment-variable substitution.

---

# 1. Critical Clarification

This project is being developed from scratch in the current environment, but it is **not intended to become a separate standalone frontend architecture**.

The final code must be structured so it can later be pushed into and integrated with the office repository structure:

```text
Forge-X-Web/
```

Therefore:

- backend is greenfield,
- orchestrator frontend module is greenfield,
- frontend must follow the target `Forge-X-Web` repository structure,
- environment variables must be explicitly defined for both local and office environments,
- no office-only hard-coded paths, URLs, credentials, imports, or assumptions are allowed,
- the code must be portable through Git by changing configuration rather than rewriting source code.

The coding agent must therefore build the implementation as:

```text
LOCAL DEVELOPMENT
        |
        | same source code
        v
GIT PUSH
        |
        v
OFFICE ENVIRONMENT
        |
        | environment-specific .env/configuration
        v
FORGE-X-WEB + ORCHESTRATOR
```

The **source tree remains stable** across both environments.

---

# 2. Main Objective

Build a dynamic multi-agent workflow orchestrator using **Deep Agents**.

The system sits between:

```text
Forge-X-Web
      |
      v
Dynamic Workflow Orchestrator
      |
      +---- BA Agent
      +---- Architect Agent
      +---- Developer Agent
      +---- Product Owner Agent
      +---- QE Agent
```

The orchestrator must support:

- natural-language workflow requests,
- initial planning,
- dynamic runtime replanning,
- agent capability selection,
- structured task invocation,
- lifecycle management,
- artifact handling,
- human approvals,
- workflow persistence,
- execution events,
- React/XYFlow visualization,
- retries,
- cancellation,
- idempotency,
- auditability.

---

# 3. Architecture Ownership

## 3.1 Application owns

The application owns:

- workflow ID
- user/workspace
- workflow status
- graph nodes/edges
- plan version
- agent registry
- capabilities
- policy
- retries
- replan limits
- cycle limits
- artifacts metadata
- audit events
- cancellation
- API contracts
- authentication
- frontend synchronization

## 3.2 Deep Agents owns

Deep Agents owns:

- intelligent planning,
- tool selection,
- task decomposition,
- iterative execution,
- dynamic next-step reasoning,
- context management,
- human interaction flow,
- resumable agent execution.

Do not make the Deep Agent the business database.

---

# 4. Target Repository Model

The repository must be organized for direct portability to the office environment.

Recommended Git structure:

```text
dynamic-workflow-orchestrator/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.sample
│   │
│   ├── api/
│   ├── config/
│   ├── domain/
│   ├── models/
│   ├── services/
│   ├── registry/
│   ├── mocks/
│   └── tests/
│
├── frontend/
│   └── Forge-X-Web/
│       ├── package.json
│       ├── .env.example
│       ├── public/
│       └── src/
│           ├── config/
│           ├── routes/
│           ├── components/
│           │   └── DynamicWorkflowOrchestrator/
│           ├── hooks/
│           ├── services/
│           └── pages/
│
├── docker-compose.yml
├── README.md
└── docs/
```

### Important

The folder:

```text
frontend/Forge-X-Web/
```

must mirror the intended office frontend repository shape closely enough that its contents can later be copied/merged into the real office `Forge-X-Web` repository with minimal structural changes.

If the office repository already contains a root-level `Forge-X-Web`, the `frontend/Forge-X-Web` directory can be treated as the development fixture representing that target repository.

Do not invent a second unrelated frontend architecture.

---

# 5. Frontend Repository Target

The orchestrator UI must be implemented under:

```text
frontend/Forge-X-Web/src/components/DynamicWorkflowOrchestrator/
```

Recommended structure:

```text
frontend/Forge-X-Web/
└── src/
    ├── config/
    │   ├── axiosClient.js
    │   ├── config.js
    │   └── environment.js
    │
    ├── routes/
    │   ├── AppRoutes.jsx
    │   └── routesPath.js
    │
    ├── services/
    │   └── orchestratorApi.js
    │
    ├── hooks/
    │   ├── useOrchestratorEvents.js
    │   └── useWorkflowState.js
    │
    ├── pages/
    │   ├── DynamicWorkflowOrchestratorPage.jsx
    │   └── DynamicWorkflowOrchestratorExecution.jsx
    │
    └── components/
        └── DynamicWorkflowOrchestrator/
            ├── QueryInput/
            │   └── QueryInput.jsx
            ├── PlanSummary/
            │   └── PlanSummary.jsx
            ├── WorkflowGraph/
            │   ├── WorkflowGraph.jsx
            │   └── AgentNode.jsx
            ├── HITLPanel/
            │   ├── PendingApprovals.jsx
            │   └── ApprovalCard.jsx
            ├── ArtifactViewer/
            │   ├── ArtifactBrowser.jsx
            │   └── ArtifactPreview.jsx
            ├── AgentDetails/
            │   └── AgentDetailsPanel.jsx
            └── EventTimeline/
                └── EventTimeline.jsx
```

---

# 6. Office Repository Compatibility Rule

Every frontend source file must follow these rules:

1. No absolute local filesystem imports.
2. No imports pointing to office-only directories.
3. No hard-coded backend URLs.
4. No hard-coded Azure URLs.
5. No hard-coded workspace IDs.
6. No hard-coded user IDs.
7. No hard-coded JWT secrets.
8. No machine-specific paths.
9. All API addresses must come from environment/config.
10. All authentication behavior must be abstracted through the configurable API client.
11. Route names must be centralized in `routesPath.js`.
12. The orchestrator module must be independently mountable into the office application.

---

# 7. Frontend Environment Strategy

Create:

```text
frontend/Forge-X-Web/.env.example
frontend/Forge-X-Web/.env.local.example
frontend/Forge-X-Web/.env.office.example
```

Never commit real `.env` files containing secrets.

## 7.1 Local example

```ini
VITE_APP_ENVIRONMENT=local

VITE_ORCHESTRATOR_API_URL=http://localhost:8000

VITE_ORCHESTRATOR_API_PREFIX=/api/dynamic-workflow

VITE_ENABLE_DYNAMIC_WORKFLOW_ORCHESTRATOR=true

VITE_SSE_TRANSPORT=fetch
VITE_SSE_RECONNECT_ENABLED=true

VITE_DEFAULT_WORKSPACE_ID=
```

If the office project uses Create React App instead of Vite, use the existing office naming convention instead of blindly replacing it. The source code must access environment variables through one configuration wrapper.

---

# 8. Frontend Environment Abstraction

Never write:

```javascript
fetch("http://localhost:8000/api/...")
```

or:

```javascript
axios.get("https://office-url/api/...")
```

inside components.

Instead:

```text
src/config/config.js
        |
        v
environment variable
        |
        v
orchestratorApi.js
        |
        v
components
```

Example:

```javascript
export function getOrchestratorApiBaseUrl() {
  return environment.orchestratorApiUrl;
}
```

The exact environment variable prefix must match the frontend build system used by the office repository.

---

# 9. Authentication Portability

The local frontend must provide an authentication abstraction.

The office implementation will later reuse the actual authentication utilities already present in `Forge-X-Web`.

Create:

```text
src/config/axiosClient.js
```

as an abstraction-compatible API client.

During local development it may use a development JWT or local auth implementation.

When moved to the office repository, this file should either:

- be replaced by the existing office `axiosClient.js`, or
- be merged so the existing authentication/interceptor behavior is retained.

The orchestrator business components must not directly manipulate JWTs.

---

# 10. Frontend Route Compatibility

Create:

```text
src/routes/routesPath.js
```

with:

```javascript
DYNAMIC_WORKFLOW_ORCHESTRATOR
DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL
```

Create routes in:

```text
src/routes/AppRoutes.jsx
```

Example:

```jsx
<Route
  path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR}
  element={<DynamicWorkflowOrchestratorPage />}
/>

<Route
  path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL}
  element={<DynamicWorkflowOrchestratorExecution />}
/>
```

These routes must be additive.

Do not restructure unrelated application routes.

---

# 11. Backend Environment Strategy

Create:

```text
backend/.env.sample
backend/.env.local.example
backend/.env.office.example
```

The real environment file must never be committed.

Example:

```ini
APP_ENV=local
APP_HOST=0.0.0.0
APP_PORT=8000

DEEP_AGENT_MODEL=
DEEP_AGENT_MODEL_PROVIDER=

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=
AZURE_OPENAI_DEPLOYMENT_NAME=

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=dwf_orchestrator

JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=3600

DWF_AGENT_REGISTRY_PATH=backend/registry/agents.json

DWF_MAX_REPLAN_ITERATIONS=6
DWF_MAX_TOTAL_AGENT_INVOCATIONS=30
DWF_MAX_AGENT_REINVOCATIONS=3
DWF_MAX_WORKFLOW_NODES=50
DWF_MAX_WORKFLOW_DURATION_SECONDS=3600
DWF_ARTIFACT_INLINE_MAX_BYTES=2048

DWF_EVENT_HEARTBEAT_SECONDS=30
DWF_EVENT_REPLAY_HOURS=24

AGENT_MODE=mock

BA_AGENT_BASE_URL=http://localhost:7101/api
ARCHITECT_AGENT_BASE_URL=http://localhost:7102/api
DEVELOPER_AGENT_BASE_URL=http://localhost:7103/api
PO_AGENT_BASE_URL=http://localhost:7104/api
QE_AGENT_BASE_URL=http://localhost:7105/api
```

Office values will replace these through the office environment's configuration.

---

# 12. Local vs Office Configuration Matrix

| Setting | Local | Office |
|---|---|---|
| Backend URL | `localhost:8000` | Office orchestrator URL |
| MongoDB | local Docker/local cluster | Office MongoDB |
| Agent mode | mock/live mix | real agents |
| BA URL | local mock | BA Function App |
| Architect URL | local mock | Architect Function App |
| Dev URL | local mock | Dev Function App |
| PO URL | local mock | PO Function App |
| QE URL | local mock | QE Function App |
| JWT | local secret/test auth | existing office auth |
| Model endpoint | local-configured | office Azure/model endpoint |
| Frontend API URL | localhost | office environment URL |
| Authentication | local adapter | existing office authentication |
| Artifact backend | local Mongo/GridFS | office-configured storage |

The source code should remain unchanged wherever possible.

---

# 13. Complete Backend Structure

```text
backend/
├── app.py
├── requirements.txt
├── pyproject.toml
├── .env.sample
│
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── routes_plan.py
│   ├── routes_execute.py
│   ├── routes_workflow.py
│   ├── routes_events.py
│   ├── routes_agents.py
│   ├── routes_hitl.py
│   ├── routes_artifacts.py
│   ├── routes_cancel.py
│   └── routes_health.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── domain/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── planner.py
│   ├── replanner.py
│   ├── orchestration_policy.py
│   ├── agent_tools.py
│   ├── response_normalizer.py
│   ├── workflow_graph.py
│   ├── hitl.py
│   ├── cancellation.py
│   └── skill_manager.py
│
├── models/
│   ├── agents.py
│   ├── workflow.py
│   ├── graph.py
│   ├── events.py
│   ├── artifacts.py
│   ├── hitl.py
│   └── errors.py
│
├── services/
│   ├── deep_agent_service.py
│   ├── agent_registry.py
│   ├── agent_client.py
│   ├── mock_agent_client.py
│   ├── mongo.py
│   ├── workflow_repository.py
│   ├── event_repository.py
│   ├── artifact_store.py
│   ├── checkpoint_store.py
│   ├── auth.py
│   ├── idempotency.py
│   ├── retry.py
│   └── event_stream.py
│
├── registry/
│   └── agents.json
│
├── mocks/
│   ├── ba_mock.py
│   ├── architect_mock.py
│   ├── developer_mock.py
│   ├── po_mock.py
│   └── qe_mock.py
│
└── tests/
    ├── unit/
    ├── contract/
    ├── integration/
    └── e2e/
```

---

# 14. Deep Agent Framework

The implementation must use the **Deep Agents framework** as the orchestration agent framework.

The Deep Agent receives:

- user query,
- current workflow state summary,
- current plan,
- execution history,
- available agent task tools,
- artifact references,
- policy constraints.

It performs intelligent reasoning and chooses the appropriate registered task tool.

The application remains responsible for validating the tool action.

---

# 15. Deep Agent System Prompt

Use a dedicated system prompt.

It must communicate:

```text
You are the Dynamic Workflow Orchestrator.

Your objective is to complete the business workflow requested by
the user using registered agent task tools.

Rules:

1. Only use registered task tools.
2. Never invent agents or capabilities.
3. Never call lifecycle/admin operations as business tools.
4. Respect dependencies.
5. Respect human approval requirements.
6. Use artifact references rather than copying large artifacts.
7. Request additional agent work only through structured actions.
8. Do not continue indefinitely.
9. Do not claim execution succeeded without tool confirmation.
10. Prefer existing artifacts instead of regenerating them.
11. Stay within workflow limits.
12. Never expose secrets or internal credentials.
```

---

# 16. Agent Registry

Create:

```text
backend/registry/agents.json
```

with all five agents.

Example:

```json
{
  "agents": [
    {
      "agent_id": "business-analyst",
      "display_name": "Business Analyst Agent",
      "contract_version": "1.0.0",
      "purpose": "Requirements analysis and business documentation",
      "capabilities": [
        "requirements_analysis",
        "brd_generation",
        "feedback_incorporation",
        "jira_query",
        "kb_query"
      ],
      "supported_task_types": [
        "create_brd",
        "get_synopsis",
        "edit_synopsis",
        "jira_agent"
      ],
      "status": "active",
      "contract_status": "verified",
      "invocation_enabled": true,
      "deployment_type": "http",
      "authentication_scheme": "bearer_jwt",
      "environment_bindings": {
        "local": {
          "base_url": "${BA_AGENT_BASE_URL}"
        },
        "office": {
          "base_url": "${BA_AGENT_BASE_URL}"
        }
      },
      "endpoints": {
        "task": [],
        "lifecycle": [],
        "admin": []
      }
    }
  ]
}
```

Repeat for:

```text
architect
developer
product-owner
qe
```

---

# 17. Endpoint Inventory

The coding agent must model the endpoint categories visible in the supplied API contract sheets.

For each real agent, record:

```text
name
route
method
category
request_schema
response_schema
timeout
async_supported
auth_scheme
enabled
```

Examples of task endpoints may include:

```text
create_brd
get_synopsis
edit_synopsis
jira_agent
generate_architecture
generate_design
generate_code
generate_test_strategy
```

The exact route remains configurable through the registry.

Do not hard-code routes into orchestration logic.

---

# 18. Agent Client

Create:

```text
services/agent_client.py
```

Responsibilities:

- construct URL,
- attach authentication,
- add correlation IDs,
- add workflow/node IDs,
- set timeout,
- execute request,
- handle retries,
- support async jobs,
- normalize transport errors,
- return raw response to the normalizer.

---

# 19. Lifecycle Automation

The agent runtime can automatically perform:

```text
health
create_session
task
store_conversation
get_status
cancel_job
```

The Deep Agent does not choose these operations.

---

# 20. Tool Design

Preferred Deep Agent tool model:

```text
business_analyst_task
architect_task
developer_task
product_owner_task
qe_task
```

Each tool accepts:

```json
{
  "task_type": "create_brd",
  "input_data": {}
}
```

The tool then executes:

```text
registry lookup
      |
policy
      |
agent client
      |
raw response
      |
normalizer
      |
artifact service
      |
workflow service
      |
structured result
```

---

# 21. Standard Response

```python
class NextAction(BaseModel):
    type: Literal[
        "none",
        "retry_self",
        "request_agent",
        "request_human",
        "needs_input",
        "blocked"
    ]

    agent_id: str | None = None
    task_type: str | None = None
    reason: str | None = None
    source_artifact_ref: str | None = None
```

```python
class StandardAgentResponse(BaseModel):
    status: Literal[
        "completed",
        "needs_input",
        "blocked",
        "error"
    ]

    result: dict[str, Any] = {}
    artifact_ref: str | None = None
    artifact_summary: str | None = None
    next_action: NextAction = NextAction(type="none")
    confidence: float = 1.0
    metadata: dict[str, Any] = {}
```

---

# 22. Response Adapters

Create:

```text
normalize_ba_response()
normalize_architect_response()
normalize_developer_response()
normalize_po_response()
normalize_qe_response()
```

All outputs must become `StandardAgentResponse`.

---

# 23. Workflow State

Recommended state:

```python
class WorkflowState(BaseModel):
    workflow_id: str
    workspace_id: str
    user_id: str
    query: str

    status: str
    plan_version: int

    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]

    current_node_id: str | None

    artifacts: list[ArtifactRef]
    pending_approval: dict | None

    replan_count: int
    total_agent_invocations: int
```

---

# 24. Initial Planning

Create the first version of the plan before business-agent execution.

Example:

```text
BA
 |
 v
Architect
 |
 v
Developer
 |
 v
QE
```

The system must persist:

```text
plan_version = 1
```

---

# 25. Dynamic Replanning

Example:

```text
BA
 |
 v
Architect
 |
 +----> needs BA clarification
 |
 v
Developer
```

becomes:

```text
BA
 |
 v
Architect
 |
 v
BA Revision
 |
 v
Architect Revision
 |
 v
Developer
 |
 v
QE
```

Emit:

```text
plan_updated
```

and increment:

```text
plan_version
```

---

# 26. Policy Validation

Before any proposed agent task executes:

```text
Agent exists?
Contract valid?
Enabled?
Task supported?
Capability valid?
Dependency satisfied?
HITL required?
Invocation limit exceeded?
Replan limit exceeded?
Cycle detected?
Cancelled?
```

If any mandatory rule fails, do not invoke the agent.

---

# 27. Guardrails

Use:

```ini
DWF_MAX_REPLAN_ITERATIONS=6
DWF_MAX_TOTAL_AGENT_INVOCATIONS=30
DWF_MAX_AGENT_REINVOCATIONS=3
DWF_MAX_WORKFLOW_NODES=50
DWF_MAX_WORKFLOW_DURATION_SECONDS=3600
```

---

# 28. Artifact Storage

Use an abstraction:

```text
ArtifactStore
```

Initial implementation:

```text
MongoDB GridFS
```

Interface:

```python
write_artifact()
read_artifact()
read_artifact_section()
delete_artifact()
```

Large content should return:

```text
artifact_ref
artifact_summary
```

rather than full contents.

---

# 29. MongoDB

Database:

```text
dwf_orchestrator
```

Collections:

```text
dwf_workflows
dwf_events
dwf_artifacts
dwf_idempotency
```

---

# 30. Workflow Persistence

Example:

```json
{
  "_id": "wf-123",
  "workspace_id": "1003",
  "user_id": "268",
  "query": "Create BRD and architecture",
  "status": "executing",
  "plan_version": 2,
  "nodes": [],
  "edges": [],
  "artifacts": [],
  "pending_approval": null,
  "version": 3,
  "created_at": "...",
  "updated_at": "..."
}
```

---

# 31. Event Model

Required:

```text
workflow_created
plan_created
plan_updated
node_started
node_completed
node_failed
agent_retry
artifact_written
interrupt_requested
hitl_resolved
workflow_cancelled
workflow_completed
workflow_failed
```

Every event contains:

```text
workflow_id
sequence_number
event_type
node_id
agent_id
payload
created_at
```

---

# 32. Event Streaming

Use an authenticated streaming mechanism that supports:

- headers/session authentication,
- reconnect,
- heartbeat,
- sequence tracking,
- missed-event replay.

The frontend must not depend on an always-open connection for correctness.

MongoDB event history remains authoritative.

---

# 33. REST API

```text
POST /api/dynamic-workflow/plan
POST /api/dynamic-workflow/{workflow_id}/execute

GET  /api/dynamic-workflow/{workflow_id}
GET  /api/dynamic-workflow/{workflow_id}/events
GET  /api/dynamic-workflow/{workflow_id}/artifacts/{artifact_id}

POST /api/dynamic-workflow/{workflow_id}/hitl/resume
POST /api/dynamic-workflow/{workflow_id}/cancel

GET  /api/dynamic-workflow/agents
GET  /api/dynamic-workflow/health
```

---

# 34. Execute API Behavior

Long-running execution must not require the browser to hold the POST request open for the entire workflow.

Preferred:

```text
POST execute
      |
      v
202 Accepted
      |
      v
background execution
      |
      v
event stream
```

---

# 35. Frontend API Layer

Create:

```text
frontend/Forge-X-Web/src/services/orchestratorApi.js
```

The module must consume:

```text
environment.orchestratorApiUrl
```

and never hard-code URLs.

Example functions:

```javascript
planWorkflow()
executeWorkflow()
getWorkflow()
getAgents()
resumeWorkflow()
cancelWorkflow()
getArtifact()
```

---

# 36. Frontend Event Hook

Create:

```text
frontend/Forge-X-Web/src/hooks/useOrchestratorEvents.js
```

Responsibilities:

- connect,
- authenticate,
- parse event,
- deduplicate,
- maintain last sequence,
- reconnect,
- replay missed events,
- update workflow state.

---

# 37. Frontend Graph

Use:

```text
@xyflow/react
```

Graph states:

```text
planned
ready
executing
awaiting_approval
completed
failed
blocked
cancelled
skipped
```

Dynamic plan changes must preserve execution history.

---

# 38. Frontend HITL

Display:

```text
Human Approval Required
Agent
Task
Reason
Artifact
Previous output
Feedback

Approve
Edit
Reject
```

---

# 39. Frontend Artifact Viewer

Support:

```text
Markdown
JSON
Code
Mermaid
OpenAPI
Text
```

Artifact contents should load on demand.

---

# 40. Frontend Office Integration Contract

When moved to the office laptop, the following mapping should be possible without redesign:

```text
Local:
frontend/Forge-X-Web/

Office:
Forge-X-Web/
```

The orchestrator module:

```text
src/components/DynamicWorkflowOrchestrator/
```

should be copied/merged directly.

Likewise:

```text
src/services/orchestratorApi.js
src/hooks/useOrchestratorEvents.js
src/pages/DynamicWorkflowOrchestratorPage.jsx
src/pages/DynamicWorkflowOrchestratorExecution.jsx
```

should integrate using the same relative repository conventions.

---

# 41. Office Integration Steps

After pushing to the office environment:

1. Copy/merge the orchestrator frontend module into the office `Forge-X-Web`.
2. Add route constants.
3. Add routes.
4. Reuse the office authentication client.
5. Set office frontend environment variable for orchestrator API.
6. Keep business components unchanged.
7. Set backend environment variables.
8. Update `agents.json` office URLs.
9. Verify MongoDB.
10. Run backend tests.
11. Run frontend tests.
12. Test BA -> Architect.

No source rewrite should be required merely because the deployment environment changed.

---

# 42. Backend Office Integration

The backend remains:

```text
dynamic-workflow-orchestrator/backend/
```

Office environment variables provide:

```text
real model endpoint
real MongoDB
real agent URLs
real authentication
```

The code itself should remain environment-agnostic.

---

# 43. Local Mock Mode

For local implementation:

```ini
AGENT_MODE=mock
```

All five logical agents must have mock behavior.

The registry still reflects the target production agent contracts.

Example:

```text
Business Analyst -> mock BA HTTP service
Architect        -> mock Architect HTTP service
Developer        -> mock Dev HTTP service
PO               -> mock PO HTTP service
QE               -> mock QE HTTP service
```

This should model realistic delays, failures, structured responses, and artifacts.

---

# 44. Mock Scenarios

The mock system must support:

### Normal

```text
completed
```

### Needs clarification

```text
needs_input
request_agent
```

### Human approval

```text
request_human
```

### Failure

```text
error
```

### Blocked

```text
blocked
```

### Dynamic revision

First call:

```text
needs_input
```

Second call:

```text
completed
```

---

# 45. Local Docker

Provide:

```text
docker-compose.yml
```

with:

```text
mongo
orchestrator-backend
mock-ba
mock-architect
mock-developer
mock-po
mock-qe
```

Frontend may be run using the local Node development server.

---

# 46. Local Startup

Expected developer experience:

```bash
docker compose up -d
```

Then:

```bash
cd backend
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn backend.app:app --reload --port 8000
```

Frontend:

```bash
cd frontend/Forge-X-Web
npm install
npm run dev
```

---

# 47. Complete Local Workflow

The developer enters:

```text
Create a BRD for an online payment platform,
design the architecture,
prepare implementation tasks,
and create a QA strategy.
```

Expected:

```text
Query
 ↓
Plan
 ↓
BA
 ↓
BRD artifact
 ↓
HITL
 ↓
Architect
 ↓
Architecture artifact
 ↓
Dev
 ↓
Development artifact
 ↓
QE
 ↓
Test strategy
 ↓
Complete
```

---

# 48. Dynamic Scenario

Architect responds:

```text
needs clarification
request BA
```

Expected:

```text
Plan v1:
BA -> Architect -> Dev -> QE

Plan v2:
BA -> Architect -> BA Revision -> Architect Revision -> Dev -> QE
```

Frontend must show the new nodes and plan version.

---

# 49. Required Tests

## Backend unit

- registry loading
- endpoint classification
- policy validation
- initial planner
- replanner
- cycle detection
- response normalization
- artifact handling
- retry
- cancellation
- idempotency
- HITL

## Contract

- BA
- Architect
- Developer
- PO
- QE

## Integration

- BA -> Architect
- dynamic replan
- HITL
- artifact handoff
- retry
- cancellation
- event replay

## Frontend

- routes
- query form
- plan
- graph
- dynamic graph
- HITL
- artifacts
- timeline
- reconnect

---

# 50. Final Build Order

The coding agent must follow this order.

## Phase 1 — Repository bootstrap

Create:

- backend
- frontend/Forge-X-Web
- environment files
- Docker
- documentation

## Phase 2 — Core models

Create:

- agent schemas
- workflow schemas
- graph schemas
- events
- artifacts
- HITL
- errors

## Phase 3 — Agent registry

Create:

- five agents
- categories
- capability lists
- configurable URLs

## Phase 4 — Agent client

Create:

- HTTP client
- retries
- lifecycle wrappers
- async polling
- structured errors

## Phase 5 — Deep Agent

Create:

- Deep Agent
- model configuration
- task tools
- system prompt

## Phase 6 — Planning

Create:

- initial plan
- graph
- persistence

## Phase 7 — Dynamic execution

Create:

- response normalization
- next actions
- orchestration policy
- replanning
- cycle protection

## Phase 8 — Mongo

Create:

- workflow repository
- event repository
- idempotency

## Phase 9 — Artifacts

Create:

- GridFS artifact store
- artifact references
- read sections

## Phase 10 — HITL

Create:

- checkpoint support
- approval
- edit
- reject
- resume

## Phase 11 — Events

Create:

- stream
- replay
- reconnect
- sequence handling

## Phase 12 — Frontend

Create:

- query
- plan
- graph
- node detail
- timeline
- artifacts
- HITL

## Phase 13 — Mock agent integration

Run complete local workflows.

## Phase 14 — Office portability validation

Verify:

- `.env` substitution,
- URL configuration,
- frontend folder compatibility,
- API integration,
- route integration,
- authentication swap,
- real-agent URL replacement.

## Phase 15 — Hardening

Add:

- security
- performance
- observability
- load tests
- documentation

---

# 51. Definition of Done

## Backend

- [ ] FastAPI starts locally
- [ ] MongoDB persists workflows
- [ ] Deep Agent executes registered tools
- [ ] all five agents are registered
- [ ] mock agents execute locally
- [ ] task/lifecycle/admin separation works
- [ ] initial plan works
- [ ] dynamic replanning works
- [ ] guardrails work
- [ ] HITL works
- [ ] artifacts work
- [ ] events work
- [ ] replay works
- [ ] retries work
- [ ] cancellation works
- [ ] errors are structured
- [ ] tests pass

## Frontend

- [ ] `frontend/Forge-X-Web` builds
- [ ] orchestrator routes work
- [ ] query screen works
- [ ] plan screen works
- [ ] XYFlow works
- [ ] dynamic graph updates work
- [ ] HITL UI works
- [ ] artifact viewer works
- [ ] timeline works
- [ ] event reconnect works
- [ ] no hard-coded environment URLs exist

## Portability

- [ ] local `.env` works
- [ ] office `.env` template exists
- [ ] agent URLs are configurable
- [ ] backend URL is configurable
- [ ] Mongo URI is configurable
- [ ] model endpoint is configurable
- [ ] authentication integration is replaceable
- [ ] frontend module can be merged into office `Forge-X-Web`
- [ ] source code does not depend on office-only paths

---

# 52. Final Architecture

```text
                       +----------------------+
                       |   Forge-X-Web        |
                       |   React Frontend     |
                       +----------+-----------+
                                  |
                         configurable API URL
                                  |
                                  v
                       +----------------------+
                       | FastAPI Orchestrator |
                       +----------+-----------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             Workflow Services            Deep Agent
                    |                           |
                    |                   +-------+-------+
                    |                   |               |
                    |               Planning        Tools
                    |                                   |
                    |             +------+------+------+------+------+
                    |             |      |      |      |            |
                    |             v      v      v      v            v
                    |             BA Architect Dev    PO           QE
                    |             |      |      |      |            |
                    |             +------+------+------+------+------+
                    |                           |
                    v                           v
              MongoDB / GridFS             HTTP Agents
                    |
                    +---- workflow state
                    +---- event history
                    +---- artifacts
                    +---- idempotency
```

---

# 53. Final Portability Principle

The most important implementation rule is:

> **Develop locally, but code against the same target repository and configuration boundaries that will be used in the office environment.**

Therefore:

```text
LOCAL CODE
   |
   +-- frontend/Forge-X-Web
   +-- backend
   +-- .env.local
   +-- mock agents
   |
   v
Git
   |
   v
OFFICE
   |
   +-- Forge-X-Web existing repository
   +-- office .env
   +-- real agent URLs
   +-- real authentication
   +-- office MongoDB
   +-- office model endpoint
```

The implementation should require **configuration changes, not architectural rewrites**, when moved to the office environment.

---

# 54. Final Success Scenario

A fresh clone of this repository must support:

```text
clone
  ↓
configure local .env
  ↓
docker compose up
  ↓
run backend
  ↓
run frontend/Forge-X-Web
  ↓
enter workflow query
  ↓
Deep Agent plans
  ↓
BA executes
  ↓
Architect executes
  ↓
dynamic replan if needed
  ↓
Developer executes
  ↓
QE executes
  ↓
artifacts stored
  ↓
events streamed
  ↓
workflow graph updates
  ↓
workflow completes
```

Then the same Git repository should be capable of being moved to the office environment by:

```text
change environment variables
change agent endpoints
reuse office authentication
merge/use the same Forge-X-Web module
```

without redesigning the orchestrator.

---

# 55. Final Rule for the Coding Agent

Before writing code, the coding agent must read this specification completely and implement in the stated order.

It must not assume access to any prior repository.

It must not invent office-only dependencies.

It must not hard-code local-only values.

It must not create a disposable frontend.

It must build the frontend under the target:

```text
frontend/Forge-X-Web/
```

structure so the implementation can later be pushed/merged into the actual office `Forge-X-Web` repository.

The implementation target is therefore:

> **Fresh local greenfield development with production-oriented repository structure and direct office-environment portability.**
