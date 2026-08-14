from pydantic import BaseModel, Field
from typing import Literal, Any


class GraphNodePosition(BaseModel):
    x: float = 0.0
    y: float = 0.0


class GraphNodeData(BaseModel):
    label: str
    agent_id: str
    display_name: str
    task_type: str
    status: str
    plan_version: int = 1
    execution_time_ms: float | None = None
    artifact_id: str | None = None
    artifact_name: str | None = None
    error_message: str | None = None
    hitl_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class XYFlowNode(BaseModel):
    id: str
    type: str = "agentNode"
    position: GraphNodePosition = Field(default_factory=GraphNodePosition)
    data: GraphNodeData


class XYFlowEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False
    label: str | None = None
    style: dict[str, Any] = Field(default_factory=dict)


class WorkflowGraphModel(BaseModel):
    nodes: list[XYFlowNode] = Field(default_factory=list)
    edges: list[XYFlowEdge] = Field(default_factory=list)
