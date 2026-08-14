from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    # LLM / Deep Agent Provider
    deep_agent_model: str = Field(default="gpt-4o", alias="DEEP_AGENT_MODEL")
    deep_agent_model_provider: str = Field(default="mock", alias="DEEP_AGENT_MODEL_PROVIDER")
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="2024-05-01-preview", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_name: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT_NAME")

    # Persistence
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="dwf_orchestrator", alias="MONGODB_DATABASE")
    persistence_mode: str = Field(default="auto", alias="PERSISTENCE_MODE")  # auto | mongo | memory

    # Security
    jwt_secret: str = Field(default="dwf_super_secret_local_dev_jwt_key_32bytes_min_length_1234", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_seconds: int = Field(default=86400, alias="JWT_EXPIRY_SECONDS")

    # Registry & Limits
    dwf_agent_registry_path: str = Field(default="registry/agents.json", alias="DWF_AGENT_REGISTRY_PATH")
    dwf_max_replan_iterations: int = Field(default=6, alias="DWF_MAX_REPLAN_ITERATIONS")
    dwf_max_total_agent_invocations: int = Field(default=30, alias="DWF_MAX_TOTAL_AGENT_INVOCATIONS")
    dwf_max_agent_reinvocations: int = Field(default=3, alias="DWF_MAX_AGENT_REINVOCATIONS")
    dwf_max_workflow_nodes: int = Field(default=50, alias="DWF_MAX_WORKFLOW_NODES")
    dwf_max_workflow_duration_seconds: int = Field(default=3600, alias="DWF_MAX_WORKFLOW_DURATION_SECONDS")
    dwf_artifact_inline_max_bytes: int = Field(default=2048, alias="DWF_ARTIFACT_INLINE_MAX_BYTES")

    # Events
    dwf_event_heartbeat_seconds: int = Field(default=15, alias="DWF_EVENT_HEARTBEAT_SECONDS")
    dwf_event_replay_hours: int = Field(default=24, alias="DWF_EVENT_REPLAY_HOURS")

    # Agent Mode & URLs
    agent_mode: str = Field(default="mock", alias="AGENT_MODE")  # mock | live
    ba_agent_base_url: str = Field(default="http://localhost:7101/api", alias="BA_AGENT_BASE_URL")
    architect_agent_base_url: str = Field(default="http://localhost:7102/api", alias="ARCHITECT_AGENT_BASE_URL")
    developer_agent_base_url: str = Field(default="http://localhost:7103/api", alias="DEVELOPER_AGENT_BASE_URL")
    po_agent_base_url: str = Field(default="http://localhost:7104/api", alias="PO_AGENT_BASE_URL")
    qe_agent_base_url: str = Field(default="http://localhost:7105/api", alias="QE_AGENT_BASE_URL")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
