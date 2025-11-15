"""Deployment and agent instance models for runtime integration."""

from datetime import datetime
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, HttpUrl, Field


class AgentEndpoint(BaseModel):
    """Runtime endpoint for a deployed agent/tool."""

    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "POST"
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[Literal["none", "bearer", "api_key", "basic"]] = "none"
    health_check_url: Optional[HttpUrl] = None
    timeout_ms: int = Field(default=30000, ge=1000, le=600000)


class DeploymentStatus(BaseModel):
    """Status of a deployed agent instance."""

    status: Literal["running", "stopped", "error", "deploying", "unknown"]
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    uptime_seconds: Optional[int] = None
    request_count: Optional[int] = None
    avg_latency_ms: Optional[float] = None


class DeploymentMetadata(BaseModel):
    """Metadata about the deployment platform."""

    platform: Literal["agno", "langserve", "custom", "docker", "kubernetes", "aws_lambda", "gcp_cloud_run"]
    platform_version: Optional[str] = None
    deployed_by: Optional[str] = None
    deployment_config: Optional[Dict] = None
    tags: List[str] = Field(default_factory=list)


class ToolDeployment(BaseModel):
    """A deployed instance of a tool/agent."""

    # Identity
    deployment_id: str
    tool_name: str
    subagent_name: str

    # Deployment info
    deployment_name: str
    description: Optional[str] = None
    endpoint: AgentEndpoint
    metadata: DeploymentMetadata

    # Status
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime

    # Environment
    environment: Literal["production", "staging", "development", "testing"] = "development"
    region: Optional[str] = None

    # Resource limits (for monitoring)
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None


class DeploymentCreate(BaseModel):
    """Request to register a new deployment."""

    tool_name: str
    subagent_name: str
    deployment_name: str
    description: Optional[str] = None
    endpoint: AgentEndpoint
    metadata: DeploymentMetadata
    environment: Literal["production", "staging", "development", "testing"] = "development"
    region: Optional[str] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None


class DeploymentUpdate(BaseModel):
    """Update deployment information."""

    description: Optional[str] = None
    endpoint: Optional[AgentEndpoint] = None
    status: Optional[DeploymentStatus] = None
    environment: Optional[Literal["production", "staging", "development", "testing"]] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None


class DeploymentResponse(BaseModel):
    """Deployment information response."""

    deployment_id: str
    tool_name: str
    subagent_name: str
    deployment_name: str
    description: Optional[str] = None
    endpoint: AgentEndpoint
    metadata: DeploymentMetadata
    status: DeploymentStatus
    environment: str
    region: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Aggregated tool info
    tool_display_name: Optional[str] = None
    tool_category: Optional[str] = None


class DeploymentSearchRequest(BaseModel):
    """Search for deployments."""

    tool_name: Optional[str] = None
    subagent_name: Optional[str] = None
    platform: Optional[str] = None
    environment: Optional[Literal["production", "staging", "development", "testing"]] = None
    status: Optional[Literal["running", "stopped", "error", "deploying", "unknown"]] = None
    region: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DeploymentSearchResponse(BaseModel):
    """Search results for deployments."""

    results: List[DeploymentResponse]
    total: int
    limit: int
    offset: int


class HealthCheckRequest(BaseModel):
    """Request to update health status."""

    status: Literal["running", "stopped", "error", "deploying", "unknown"]
    error_message: Optional[str] = None
    uptime_seconds: Optional[int] = None
    request_count: Optional[int] = None
    avg_latency_ms: Optional[float] = None


# Agno-specific models
class AgnoAgentDeployment(BaseModel):
    """Agno-specific deployment information."""

    agent_id: str
    agent_name: str
    tools: List[str]  # Tool names used by this agent
    endpoint_url: HttpUrl
    api_key_required: bool = True
    session_enabled: bool = True
    memory_enabled: bool = True

    # Map to generic deployment
    environment: Literal["production", "staging", "development", "testing"] = "production"
    region: Optional[str] = None


class AgnoIntegrationConfig(BaseModel):
    """Configuration for Agno integration."""

    agno_api_url: HttpUrl
    agno_api_key: str
    auto_register_deployments: bool = True
    health_check_interval_seconds: int = Field(default=60, ge=30, le=3600)
    sync_agent_metadata: bool = True
