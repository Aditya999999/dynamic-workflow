from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime


class PendingApproval(BaseModel):
    approval_id: str
    node_id: str
    agent_id: str
    task_type: str
    reason: str
    artifact_id: str | None = None
    artifact_summary: str | None = None
    proposed_output: dict[str, Any] = Field(default_factory=dict)
    feedback_requested: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalResolution(BaseModel):
    decision: Literal["approved", "edited", "rejected"]
    feedback: str | None = None
    edited_data: dict[str, Any] | None = None
    user_id: str = "default_user"
    resolved_at: datetime = Field(default_factory=datetime.utcnow)


class ResumePayload(BaseModel):
    decision: Literal["approved", "edited", "rejected"]
    feedback: str | None = None
    edited_data: dict[str, Any] | None = None
