"""Pydantic models for SubAgent metadata."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class SubAgentMetadata(BaseModel):
    """Core metadata for a SubAgent."""

    name: str = Field(..., description="Unique name of the subagent")
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")
    description: str = Field(..., description="Brief description of the subagent")
    author: Optional[str] = Field(None, description="Author name or organization")
    license: Optional[str] = Field(None, description="License (e.g., MIT, Apache-2.0)")
    domain: str = Field(..., description="Primary domain (e.g., research, coding, critique)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    capabilities: List[str] = Field(
        default_factory=list, description="List of capabilities this subagent provides"
    )
    use_cases: List[str] = Field(
        default_factory=list, description="Example use cases for routing"
    )
    priority: int = Field(
        default=0, ge=0, le=100, description="Priority for search ranking (0-100)"
    )


class Installation(BaseModel):
    """Installation method metadata."""

    method: Literal["git", "npm", "pip", "docker", "remote"] = Field(
        ..., description="Installation method type"
    )

    # Git-specific fields
    repository: Optional[str] = Field(None, description="Git repository URL")
    branch: Optional[str] = Field(None, description="Git branch name")
    commit: Optional[str] = Field(None, description="Specific commit hash")

    # Package manager fields
    package_name: Optional[str] = Field(None, description="NPM/Pip package name")
    package_version: Optional[str] = Field(None, description="Package version")
    registry_url: Optional[str] = Field(None, description="Custom registry URL")

    # Docker-specific fields
    image: Optional[str] = Field(None, description="Docker image name with tag")

    # Remote API fields
    url: Optional[str] = Field(None, description="Remote API URL")
    auth: Optional[Dict[str, str]] = Field(None, description="Authentication config")

    # Post-install
    post_install_commands: List[str] = Field(
        default_factory=list, description="Commands to run after installation"
    )

    @field_validator("method")
    @classmethod
    def validate_method_fields(cls, v: str) -> str:
        """Validate that required fields for each method are present."""
        # Note: This is a basic validator. Full validation should check field presence
        return v


class Activation(BaseModel):
    """Activation/execution configuration."""

    activation_type: Literal["stdio", "http", "mcp", "sse", "websocket"] = Field(
        ..., description="Type of activation protocol"
    )

    # Command execution (stdio, http)
    command: Optional[str] = Field(None, description="Command to execute")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    working_dir: Optional[str] = Field(None, description="Working directory for execution")

    # Environment variables
    env_vars: Dict[str, Any] = Field(
        default_factory=dict, description="Environment variables (with required/optional flags)"
    )

    # Health check (http, sse, websocket)
    health_check: Optional[Dict[str, Any]] = Field(
        None, description="Health check configuration"
    )

    # Protocol-specific
    protocol: Optional[str] = Field(None, description="Protocol name (e.g., MCP)")
    capabilities: List[str] = Field(default_factory=list, description="Protocol capabilities")

    # Connection info (remote services)
    url: Optional[str] = Field(None, description="Service URL (for http/sse/websocket)")
    auth: Optional[Dict[str, str]] = Field(None, description="Authentication config")


class Dependency(BaseModel):
    """Dependency specification."""

    dep_type: Literal["python", "npm", "system", "api"] = Field(
        ..., description="Dependency type"
    )
    name: str = Field(..., description="Dependency name")
    version: Optional[str] = Field(None, description="Version constraint")
    required: bool = Field(default=True, description="Whether this dependency is required")
    description: Optional[str] = Field(None, description="Description of the dependency")


class Example(BaseModel):
    """Usage example."""

    input: str = Field(..., description="Example input")
    output: str = Field(..., description="Expected output")
    description: Optional[str] = Field(None, description="Description of the example")


class SubAgent(BaseModel):
    """Complete SubAgent definition."""

    metadata: SubAgentMetadata
    prompts: List["PromptTemplate"] = Field(default_factory=list)
    interface: Optional["InterfaceSpec"] = None
    installations: List[Installation] = Field(default_factory=list)
    activations: List[Activation] = Field(default_factory=list)
    examples: List[Example] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)


class SubAgentCreate(BaseModel):
    """Request model for creating a SubAgent."""

    metadata: SubAgentMetadata
    prompts: List[Dict[str, Any]] = Field(default_factory=list)
    interface: Optional[Dict[str, Any]] = None
    installations: List[Installation] = Field(default_factory=list)
    activations: List[Activation] = Field(default_factory=list)
    examples: List[Example] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)


class SubAgentResponse(SubAgent):
    """Response model for SubAgent with additional metadata."""

    id: int = Field(..., description="Database ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# Forward references
from .interface import InterfaceSpec
from .prompt import PromptTemplate

SubAgent.model_rebuild()
