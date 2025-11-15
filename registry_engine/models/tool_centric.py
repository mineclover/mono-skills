"""Redesigned Pydantic models - Tool-centric architecture."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Installation Models
# ============================================================================

class Installation(BaseModel):
    """Installation method for a SubAgent package."""

    method: Literal["pip", "npm", "yarn", "cargo", "go", "docker", "binary", "git", "remote"] = Field(
        ..., description="Installation method"
    )
    platform_id: str = Field(..., description="Unique platform identifier (e.g., 'pip-python', 'npm-node')")

    # Package managers
    package_name: Optional[str] = Field(None, description="Package name")
    package_version: Optional[str] = Field(None, description="Package version constraint")
    registry_url: Optional[HttpUrl] = Field(None, description="Custom registry URL")

    # Git
    repository: Optional[HttpUrl] = Field(None, description="Git repository URL")
    branch: Optional[str] = Field(None, description="Git branch")
    commit: Optional[str] = Field(None, description="Git commit hash")

    # Docker
    image: Optional[str] = Field(None, description="Docker image with tag")

    # Binary
    download_url: Optional[HttpUrl] = Field(None, description="Binary download URL")
    checksum: Optional[str] = Field(None, description="File checksum for verification")

    # Remote API
    api_endpoint: Optional[HttpUrl] = Field(None, description="Remote API endpoint")
    auth_method: Optional[str] = Field(None, description="Authentication method")

    # Common
    requires_install: bool = Field(True, description="Whether installation is required (false for remote)")
    post_install_commands: List[str] = Field(default_factory=list, description="Commands to run after install")
    platforms: Optional[List[str]] = Field(None, description="Supported platforms (linux, darwin, win32)")
    arch: Optional[List[str]] = Field(None, description="Supported architectures (x64, arm64)")


# ============================================================================
# Activation Models
# ============================================================================

class EnvVar(BaseModel):
    """Environment variable specification."""

    required: bool = Field(default=False, description="Whether this env var is required")
    description: Optional[str] = Field(None, description="Description of the env var")
    default: Optional[str] = Field(None, description="Default value")


class Activation(BaseModel):
    """Activation/execution method."""

    type: Literal[
        "cli",
        "cli_subcommand",
        "http_server",
        "http_endpoint",
        "grpc",
        "websocket",
        "sse",
        "stdio",
        "library"
    ] = Field(..., description="Activation type")

    platform_id: Optional[str] = Field(None, description="Associated installation platform")

    # CLI
    command: Optional[str] = Field(None, description="Command to execute")
    subcommand: Optional[str] = Field(None, description="Subcommand (for cli_subcommand type)")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    working_dir: Optional[str] = Field(None, description="Working directory")

    # HTTP Server
    host: Optional[str] = Field(None, description="Server host")
    port: Optional[int] = Field(None, description="Server port")
    health_check_endpoint: Optional[str] = Field(None, description="Health check endpoint")

    # HTTP Endpoint
    base_url: Optional[HttpUrl] = Field(None, description="Base URL for HTTP endpoint")
    endpoint: Optional[str] = Field(None, description="API endpoint path")
    method: Optional[str] = Field(None, description="HTTP method")
    requires_server: bool = Field(False, description="Whether a server needs to be started first")
    server_command: Optional[str] = Field(None, description="Command to start server")

    # SSE/WebSocket
    url: Optional[HttpUrl] = Field(None, description="Connection URL")
    event_type: Optional[str] = Field(None, description="Event type for SSE")

    # Common
    env_vars: Dict[str, EnvVar] = Field(default_factory=dict, description="Environment variables")
    timeout: Optional[int] = Field(None, description="Execution timeout in seconds")


# ============================================================================
# Prompt Models
# ============================================================================

class ToolPrompt(BaseModel):
    """Prompt template for using a tool."""

    name: str = Field(..., description="Prompt name (e.g., 'default', 'detailed')")
    description: Optional[str] = Field(None, description="Prompt description")

    # Template type
    template_type: Literal["chat", "string", "few_shot"] = Field(
        default="chat", description="Template type"
    )

    # Chat template
    system_message: Optional[str] = Field(None, description="System message for chat templates")
    human_message_template: str = Field(..., description="Human message template")
    ai_message_prefix: Optional[str] = Field(None, description="AI message prefix")

    # Few-shot examples
    examples: List[Dict[str, str]] = Field(default_factory=list, description="Few-shot examples")

    # Variables
    input_variables: List[str] = Field(default_factory=list, description="Template input variables")
    partial_variables: Dict[str, Any] = Field(default_factory=dict, description="Partial variables")

    # Raw template (Jinja2)
    template: str = Field(..., description="Full template in Jinja2 format")


# ============================================================================
# Schema Models
# ============================================================================

class ParameterSchema(BaseModel):
    """JSON Schema for tool parameters."""

    type: str = Field(default="object", description="Schema type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Parameter properties")
    required: List[str] = Field(default_factory=list, description="Required parameters")
    additionalProperties: bool = Field(default=False, description="Allow additional properties")


class StructuredOutputSchema(BaseModel):
    """Structured output schema for a tool."""

    name: str = Field(..., description="Schema name")
    description: Optional[str] = Field(None, description="Schema description")

    # JSON Schema (universal)
    json_schema: Dict[str, Any] = Field(..., description="JSON Schema definition")

    # Language-specific schemas
    pydantic_code: Optional[str] = Field(None, description="Pydantic class code (Python)")
    typescript_type: Optional[str] = Field(None, description="TypeScript type definition")

    # Examples
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example outputs")


# ============================================================================
# Tool Model (Primary Entity)
# ============================================================================

class Tool(BaseModel):
    """Individual tool/function - primary search target."""

    # Identity
    name: str = Field(..., description="Unique tool name (e.g., 'web_search')")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Tool description")

    # Classification
    category: str = Field(..., description="Tool category (search, analysis, generation)")
    tags: List[str] = Field(default_factory=list, description="Tags for search")

    # SubAgent reference (where to install from)
    subagent_name: str = Field(..., description="Parent SubAgent name")
    subagent_version: str = Field(..., description="SubAgent version")

    # Prompts (how to use this tool)
    prompts: List[ToolPrompt] = Field(default_factory=list, description="Usage prompts")

    # Interface
    parameters: ParameterSchema = Field(..., description="Input parameters schema")
    structured_output: Optional[StructuredOutputSchema] = Field(None, description="Output schema")

    # Execution (can differ from SubAgent)
    activations: List[Activation] = Field(default_factory=list, description="Execution methods")
    inherit_activation: bool = Field(True, description="Inherit SubAgent activation if empty")

    # Protocol info
    protocol: str = Field(default="langchain", description="Protocol (langchain, mcp, openai-function)")
    implementation_hint: Optional[str] = Field(None, description="Implementation path hint")


class ToolCreate(BaseModel):
    """Request model for creating a Tool."""

    name: str
    display_name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    subagent_name: str
    subagent_version: str
    prompts: List[ToolPrompt] = Field(default_factory=list)
    parameters: ParameterSchema
    structured_output: Optional[StructuredOutputSchema] = None
    activations: List[Activation] = Field(default_factory=list)
    inherit_activation: bool = True
    protocol: str = "langchain"
    implementation_hint: Optional[str] = None


class ToolResponse(Tool):
    """Response model for Tool with metadata."""

    id: int = Field(..., description="Database ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# SubAgent Model (Package/Installation Unit)
# ============================================================================

class SubAgentMetadata(BaseModel):
    """Core metadata for a SubAgent package."""

    name: str = Field(..., description="Unique SubAgent name")
    version: str = Field(..., description="Semantic version")
    description: str = Field(..., description="SubAgent description")
    author: Optional[str] = Field(None, description="Author")
    license: Optional[str] = Field(None, description="License")

    # Classification
    category: str = Field(..., description="Primary category")
    tags: List[str] = Field(default_factory=list, description="Tags")

    # Priority for search ranking
    priority: int = Field(default=0, ge=0, le=100, description="Search priority (0-100)")


class Dependency(BaseModel):
    """Dependency specification."""

    dep_type: Literal["python", "npm", "system", "api"] = Field(..., description="Dependency type")
    name: str = Field(..., description="Dependency name")
    version: Optional[str] = Field(None, description="Version constraint")
    required: bool = Field(default=True, description="Whether required")
    description: Optional[str] = Field(None, description="Description")


class SubAgent(BaseModel):
    """SubAgent package - collection of tools."""

    metadata: SubAgentMetadata

    # Installation methods (multiple options)
    installations: List[Installation] = Field(default_factory=list, description="Installation methods")

    # Execution methods (can be installation-specific)
    activations: List[Activation] = Field(default_factory=list, description="Activation methods")

    # Dependencies
    dependencies: List[Dependency] = Field(default_factory=list, description="Dependencies")

    # Tools provided (reference)
    provides_tools: List[str] = Field(default_factory=list, description="Tool names provided")


class SubAgentCreate(BaseModel):
    """Request model for creating a SubAgent."""

    metadata: SubAgentMetadata
    installations: List[Installation] = Field(default_factory=list)
    activations: List[Activation] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    provides_tools: List[str] = Field(default_factory=list)


class SubAgentResponse(SubAgent):
    """Response model for SubAgent with metadata."""

    id: int = Field(..., description="Database ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
