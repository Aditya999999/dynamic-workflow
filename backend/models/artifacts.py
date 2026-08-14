from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime


class ArtifactMetadata(BaseModel):
    artifact_id: str
    workflow_id: str
    node_id: str | None = None
    agent_id: str
    name: str
    artifact_type: Literal["markdown", "json", "code", "mermaid", "openapi", "text", "binary"] = "markdown"
    content_type: str = "text/markdown"
    size_bytes: int = 0
    storage_backend: Literal["gridfs", "filesystem", "inline", "azure_blob"] = "gridfs"
    storage_key: str = ""
    summary: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactRef(BaseModel):
    artifact_id: str
    name: str
    artifact_type: str
    size_bytes: int = 0
    summary: str | None = None
    download_url: str | None = None


class ArtifactContentResponse(BaseModel):
    metadata: ArtifactMetadata
    content: str
    is_truncated: bool = False
    total_bytes: int = 0
