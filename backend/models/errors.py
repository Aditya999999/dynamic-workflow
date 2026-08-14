from pydantic import BaseModel, Field
from typing import Any


class APIErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int = 400
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowError(Exception):
    def __init__(self, message: str, code: str = "WORKFLOW_ERROR", details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class PolicyViolationError(WorkflowError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="POLICY_VIOLATION", details=details)


class AgentExecutionError(WorkflowError):
    def __init__(self, message: str, agent_id: str, details: dict[str, Any] | None = None):
        d = details or {}
        d["agent_id"] = agent_id
        super().__init__(message, code="AGENT_EXECUTION_ERROR", details=d)
