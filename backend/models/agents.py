from pydantic import BaseModel, Field
from typing import Literal, Any


class AgentEndpoint(BaseModel):
    name: str
    route: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "POST"
    category: Literal["task", "lifecycle", "admin"] = "task"
    is_primary_entrypoint: bool = False
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60
    async_supported: bool = False
    status_route: str | None = None
    auth_scheme: str = "bearer_jwt"
    enabled: bool = True

    class Config:
        extra = "ignore"


class AgentEndpoints(BaseModel):
    task: list[AgentEndpoint] = Field(default_factory=list)
    lifecycle: list[AgentEndpoint] = Field(default_factory=list)
    admin: list[AgentEndpoint] = Field(default_factory=list)


class EnvironmentBinding(BaseModel):
    base_url: str


class AgentDefinition(BaseModel):
    agent_id: str
    display_name: str
    contract_version: str = "1.0.0"
    purpose: str
    capabilities: list[str] = Field(default_factory=list)
    supported_task_types: list[str] = Field(default_factory=list)
    status: Literal["active", "inactive", "deprecated"] = "active"
    contract_status: Literal["verified", "provisional", "deprecated"] = "verified"
    invocation_enabled: bool = True
    deployment_type: Literal["http", "in_process", "mock"] = "http"
    authentication_scheme: Literal["bearer_jwt", "api_key", "none"] = "bearer_jwt"
    environment_bindings: dict[str, EnvironmentBinding] = Field(default_factory=dict)
    endpoints: AgentEndpoints = Field(default_factory=AgentEndpoints)


class AgentRegistrySchema(BaseModel):
    version: str = "1.0.0"
    agents: list[AgentDefinition] = Field(default_factory=list)
