# Dynamic Workflow Orchestrator V5 (Deep Agent Architecture)

Greenfield + Office-Repository-Compatible Multi-Agent Workflow Orchestrator built using **Deep Agents**, **FastAPI**, **MongoDB/GridFS**, and **React (`Forge-X-Web`)** with `@xyflow/react`.

---

## 🌟 Architecture Overview

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

## 🚀 Key Features

1. **Intelligent Deep Agent Loop**:
   - Natural language planning & DAG creation.
   - Dynamic runtime replanning (e.g. Architect requesting clarification from BA).
   - Tool calling across all 5 specialized agents.
2. **Human-In-The-Loop (HITL)**:
   - Automated pause & checkpointing for human signoffs.
   - Interactive ApprovalCard supporting Approval, In-place JSON Editing, or Rejection with feedback.
3. **Real-time SSE Event Streaming**:
   - Sequence tracking, automatic reconnect, and missed-event replay.
4. **Artifact Management (GridFS & In-Memory Fallback)**:
   - Full section paging, Markdown, Code, JSON, and Mermaid diagram visualization.
5. **Production & Office Portability**:
   - Zero hard-coded URLs or machine paths.
   - Single configuration file swap (`.env.local` vs `.env.office`) transitions from local mocks to Azure production microservices.

---

## 📦 Quick Start (Local Development)

### 1. Backend Startup

```bash
cd backend
pip install -r requirements.txt

# Start backend (auto in-memory / Mongo fallback + mock agents enabled)
uvicorn app:app --reload --port 8000
```

Backend API Documentation: `http://localhost:8000/docs`

### 2. Frontend Startup

```bash
cd frontend/Forge-X-Web
npm install
npm run dev
```

Frontend Application: `http://localhost:3000/orchestrator`

---

## 🧪 Running Automated Tests

Run backend unit, contract, and integration tests:

```bash
python -m pytest backend/tests -v
```

Build production frontend bundle:

```bash
cd frontend/Forge-X-Web
npm run build
```

---

## 🏢 Office Deployment Configuration Matrix

| Setting | Local Development | Office Production |
|---|---|---|
| `APP_ENV` | `local` | `production` |
| `AGENT_MODE` | `mock` | `live` |
| `MONGODB_URI` | `mongodb://localhost:27017` | Azure Cosmos DB / Mongo URI |
| `BA_AGENT_BASE_URL` | `http://localhost:7101/api` | `https://forgeX-dev-fun-ba.azurewebsites.net/api` |
| `ARCHITECT_AGENT_BASE_URL` | `http://localhost:7102/api` | `https://arch-rest-dev.azurewebsites.net/api` |
| `DEVELOPER_AGENT_BASE_URL` | `http://localhost:7103/api` | Azure Function Dev URL |
| `PO_AGENT_BASE_URL` | `http://localhost:7104/api` | Azure Function PO URL |
| `QE_AGENT_BASE_URL` | `http://localhost:7105/api` | Azure Function QE URL |
| `VITE_ORCHESTRATOR_API_URL`| `http://localhost:8000` | Office Gateway URL |

---

## 📄 License
Internal enterprise license for Coforge / Forge-X AI Platform.