from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime

EventType = Literal[
    "workflow_created",
    "plan_created",
    "plan_updated",
    "node_started",
    "node_completed",
    "node_failed",
    "agent_retry",
    "artifact_written",
    "interrupt_requested",
    "hitl_resolved",
    "workflow_cancelled",
    "workflow_completed",
    "workflow_failed",
    "heartbeat"
]


class WorkflowEvent(BaseModel):
    workflow_id: str
    sequence_number: int
    event_type: EventType
    node_id: str | None = None
    agent_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
