"""SQLAlchemy ORM models - Tool-centric architecture."""

import json
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ============================================================================
# SubAgent Models (Package/Installation)
# ============================================================================

class SubAgentModel(Base):
    """SubAgent package - installation and metadata."""

    __tablename__ = "subagents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(Text, nullable=False, default="[]")  # JSON array
    priority = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    installations = relationship("InstallationModel", back_populates="subagent", cascade="all, delete-orphan")
    activations = relationship("SubAgentActivationModel", back_populates="subagent", cascade="all, delete-orphan")
    dependencies = relationship("DependencyModel", back_populates="subagent", cascade="all, delete-orphan")
    tools = relationship("ToolModel", back_populates="subagent", cascade="all, delete-orphan")
    deployments = relationship("DeploymentModel", back_populates="subagent", cascade="all, delete-orphan")

    def get_tags(self) -> List[str]:
        return json.loads(self.tags) if self.tags else []

    def set_tags(self, tags: List[str]) -> None:
        self.tags = json.dumps(tags)


class InstallationModel(Base):
    """Installation method for a SubAgent."""

    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)

    method = Column(String(50), nullable=False)
    platform_id = Column(String(100), nullable=False, index=True)

    # Package managers
    package_name = Column(String(255), nullable=True)
    package_version = Column(String(100), nullable=True)
    registry_url = Column(String(512), nullable=True)

    # Git
    repository = Column(String(512), nullable=True)
    branch = Column(String(255), nullable=True)
    commit = Column(String(255), nullable=True)

    # Docker
    image = Column(String(512), nullable=True)

    # Binary
    download_url = Column(String(512), nullable=True)
    checksum = Column(String(255), nullable=True)

    # Remote
    api_endpoint = Column(String(512), nullable=True)
    auth_method = Column(String(100), nullable=True)

    # Common
    requires_install = Column(Boolean, default=True, nullable=False)
    post_install_commands = Column(Text, default="[]")  # JSON array
    platforms = Column(Text, default="[]")  # JSON array
    arch = Column(Text, default="[]")  # JSON array

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="installations")

    __table_args__ = (
        UniqueConstraint("subagent_id", "platform_id", name="uq_subagent_platform"),
    )

    def get_post_install_commands(self) -> List[str]:
        return json.loads(self.post_install_commands) if self.post_install_commands else []

    def set_post_install_commands(self, commands: List[str]) -> None:
        self.post_install_commands = json.dumps(commands)

    def get_platforms(self) -> List[str]:
        return json.loads(self.platforms) if self.platforms else []

    def set_platforms(self, platforms: List[str]) -> None:
        self.platforms = json.dumps(platforms)

    def get_arch(self) -> List[str]:
        return json.loads(self.arch) if self.arch else []

    def set_arch(self, arch: List[str]) -> None:
        self.arch = json.dumps(arch)


class SubAgentActivationModel(Base):
    """Activation method for a SubAgent (can be platform-specific)."""

    __tablename__ = "subagent_activations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)

    activation_type = Column(String(50), nullable=False)
    platform_id = Column(String(100), nullable=True, index=True)  # Null = all platforms

    # CLI
    command = Column(String(512), nullable=True)
    subcommand = Column(String(255), nullable=True)
    args = Column(Text, default="[]")  # JSON array
    working_dir = Column(String(512), nullable=True)

    # HTTP Server
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    health_check_endpoint = Column(String(255), nullable=True)

    # HTTP Endpoint
    base_url = Column(String(512), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    requires_server = Column(Boolean, default=False)
    server_command = Column(String(512), nullable=True)

    # SSE/WebSocket
    url = Column(String(512), nullable=True)
    event_type = Column(String(100), nullable=True)

    # Common
    env_vars = Column(Text, default="{}")  # JSON object
    timeout = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="activations")

    def get_args(self) -> List[str]:
        return json.loads(self.args) if self.args else []

    def set_args(self, args: List[str]) -> None:
        self.args = json.dumps(args)

    def get_env_vars(self) -> Dict[str, Any]:
        return json.loads(self.env_vars) if self.env_vars else {}

    def set_env_vars(self, env_vars: Dict[str, Any]) -> None:
        self.env_vars = json.dumps(env_vars)


class DependencyModel(Base):
    """Dependency specification."""

    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)

    dep_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=True)
    required = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="dependencies")


# ============================================================================
# Tool Models (Primary Entity)
# ============================================================================

class ToolModel(Base):
    """Tool - primary search target."""

    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(Text, nullable=False, default="[]")  # JSON array

    # SubAgent reference
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    subagent_version = Column(String(50), nullable=False)

    # Interface
    parameters = Column(Text, nullable=False)  # JSON Schema
    structured_output = Column(Text, nullable=True)  # JSON

    # Execution
    inherit_activation = Column(Boolean, default=True)

    # Protocol
    protocol = Column(String(100), default="langchain")
    implementation_hint = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="tools")
    prompts = relationship("ToolPromptModel", back_populates="tool", cascade="all, delete-orphan")
    activations = relationship("ToolActivationModel", back_populates="tool", cascade="all, delete-orphan")
    deployments = relationship("DeploymentModel", back_populates="tool", cascade="all, delete-orphan")

    def get_tags(self) -> List[str]:
        return json.loads(self.tags) if self.tags else []

    def set_tags(self, tags: List[str]) -> None:
        self.tags = json.dumps(tags)

    def get_parameters(self) -> Dict[str, Any]:
        return json.loads(self.parameters) if self.parameters else {}

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        self.parameters = json.dumps(parameters)

    def get_structured_output(self) -> Dict[str, Any]:
        return json.loads(self.structured_output) if self.structured_output else {}

    def set_structured_output(self, output: Dict[str, Any]) -> None:
        self.structured_output = json.dumps(output)


class ToolPromptModel(Base):
    """Prompt template for a tool."""

    __tablename__ = "tool_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), default="chat")

    # Chat template
    system_message = Column(Text, nullable=True)
    human_message_template = Column(Text, nullable=False)
    ai_message_prefix = Column(String(255), nullable=True)

    # Few-shot
    examples = Column(Text, default="[]")  # JSON array

    # Variables
    input_variables = Column(Text, default="[]")  # JSON array
    partial_variables = Column(Text, default="{}")  # JSON object

    # Raw template
    template = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tool = relationship("ToolModel", back_populates="prompts")

    __table_args__ = (
        UniqueConstraint("tool_id", "name", name="uq_tool_prompt"),
    )

    def get_examples(self) -> List[Dict[str, str]]:
        return json.loads(self.examples) if self.examples else []

    def set_examples(self, examples: List[Dict[str, str]]) -> None:
        self.examples = json.dumps(examples)

    def get_input_variables(self) -> List[str]:
        return json.loads(self.input_variables) if self.input_variables else []

    def set_input_variables(self, variables: List[str]) -> None:
        self.input_variables = json.dumps(variables)

    def get_partial_variables(self) -> Dict[str, Any]:
        return json.loads(self.partial_variables) if self.partial_variables else {}

    def set_partial_variables(self, variables: Dict[str, Any]) -> None:
        self.partial_variables = json.dumps(variables)


class ToolActivationModel(Base):
    """Activation method for a tool (can override SubAgent activation)."""

    __tablename__ = "tool_activations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)

    activation_type = Column(String(50), nullable=False)
    platform_id = Column(String(100), nullable=True, index=True)

    # CLI
    command = Column(String(512), nullable=True)
    subcommand = Column(String(255), nullable=True)
    args = Column(Text, default="[]")  # JSON array
    working_dir = Column(String(512), nullable=True)

    # HTTP Server
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    health_check_endpoint = Column(String(255), nullable=True)

    # HTTP Endpoint
    base_url = Column(String(512), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    requires_server = Column(Boolean, default=False)
    server_command = Column(String(512), nullable=True)

    # SSE/WebSocket
    url = Column(String(512), nullable=True)
    event_type = Column(String(100), nullable=True)

    # Common
    env_vars = Column(Text, default="{}")  # JSON object
    timeout = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tool = relationship("ToolModel", back_populates="activations")

    def get_args(self) -> List[str]:
        return json.loads(self.args) if self.args else []

    def set_args(self, args: List[str]) -> None:
        self.args = json.dumps(args)

    def get_env_vars(self) -> Dict[str, Any]:
        return json.loads(self.env_vars) if self.env_vars else {}

    def set_env_vars(self, env_vars: Dict[str, Any]) -> None:
        self.env_vars = json.dumps(env_vars)
