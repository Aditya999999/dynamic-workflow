from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime
from models.artifacts import ArtifactRef
from models.hitl import PendingApproval

NodeStatus = Literal[
    "planned",
    "ready",
    "executing",
    "awaiting_approval",
    "completed",
    "failed",
    "blocked",
    "cancelled",
    "skipped"
]

WorkflowStatus = Literal[
    "draft",
    "planned",
    "executing",
    "awaiting_approval",
    "completed",
    "failed",
    "cancelled"
]


class NextAction(BaseModel):
    type: Literal[
        "none",
        "retry_self",
        "request_agent",
        "request_human",
        "needs_input",
        "blocked"
    ] = "none"
    agent_id: str | None = None
    task_type: str | None = None
    reason: str | None = None
    source_artifact_ref: str | None = None
    input_patch: dict[str, Any] = Field(default_factory=dict)


class StandardAgentResponse(BaseModel):
    status: Literal["completed", "needs_input", "blocked", "error"] = "completed"
    result: dict[str, Any] = Field(default_factory=dict)
    artifact_ref: str | None = None
    artifact_summary: str | None = None
    artifact_name: str | None = None
    artifact_type: str | None = None
    next_action: NextAction = Field(default_factory=NextAction)
    confidence: float = 1.0
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    id: str
    agent_id: str
    task_type: str
    display_name: str
    status: NodeStatus = "planned"
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    artifact_refs: list[str] = Field(default_factory=list)
    plan_version: int = 1
    invocation_count: int = 0
    depends_on: list[str] = Field(default_factory=list)
    hitl_required: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    position_x: float = 0.0
    position_y: float = 0.0


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str = "dependency"
    plan_version: int = 1


class WorkflowState(BaseModel):
    workflow_id: str
    workspace_id: str = "default_workspace"
    user_id: str = "default_user"
    query: str
    status: WorkflowStatus = "draft"
    plan_version: int = 1
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    current_node_id: str | None = None
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    pending_approval: PendingApproval | None = None
    replan_count: int = 0
    total_agent_invocations: int = 0
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: str | None = None


class PlanWorkflowRequest(BaseModel):
    query: str
    workspace_id: str = "default_workspace"
    user_id: str = "default_user"
    initial_context: dict[str, Any] = Field(default_factory=dict)


class ExecuteWorkflowRequest(BaseModel):
    initial_inputs: dict[str, Any] = Field(default_factory=dict)
    auto_approve_hitl: bool = False


class WorkflowExecutionResponse(BaseModel):
    status: str = "accepted"
    workflow_id: str
    message: str = "Workflow execution started"
    plan_version: int = 1
