"""SQLAlchemy ORM models for SubAgent Registry."""

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


class SubAgentModel(Base):
    """SQLAlchemy model for SubAgent metadata."""

    __tablename__ = "subagents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    tags = Column(Text, nullable=False, default="[]")  # JSON array
    capabilities = Column(Text, nullable=False, default="[]")  # JSON array
    use_cases = Column(Text, nullable=False, default="[]")  # JSON array
    priority = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    prompts = relationship("PromptModel", back_populates="subagent", cascade="all, delete-orphan")
    interfaces = relationship(
        "InterfaceModel", back_populates="subagent", cascade="all, delete-orphan"
    )
    installations = relationship(
        "InstallationModel", back_populates="subagent", cascade="all, delete-orphan"
    )
    activations = relationship(
        "ActivationModel", back_populates="subagent", cascade="all, delete-orphan"
    )
    examples = relationship("ExampleModel", back_populates="subagent", cascade="all, delete-orphan")
    dependencies = relationship(
        "DependencyModel", back_populates="subagent", cascade="all, delete-orphan"
    )

    def get_tags(self) -> List[str]:
        """Parse tags from JSON."""
        return json.loads(self.tags) if self.tags else []

    def set_tags(self, tags: List[str]) -> None:
        """Serialize tags to JSON."""
        self.tags = json.dumps(tags)

    def get_capabilities(self) -> List[str]:
        """Parse capabilities from JSON."""
        return json.loads(self.capabilities) if self.capabilities else []

    def set_capabilities(self, capabilities: List[str]) -> None:
        """Serialize capabilities to JSON."""
        self.capabilities = json.dumps(capabilities)

    def get_use_cases(self) -> List[str]:
        """Parse use_cases from JSON."""
        return json.loads(self.use_cases) if self.use_cases else []

    def set_use_cases(self, use_cases: List[str]) -> None:
        """Serialize use_cases to JSON."""
        self.use_cases = json.dumps(use_cases)


class PromptModel(Base):
    """SQLAlchemy model for Prompt templates."""

    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    name = Column(String(255), nullable=False)
    template = Column(Text, nullable=False)
    variables = Column(Text, default="{}")  # JSON object
    format = Column(String(50), default="jinja2")
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="prompts")

    __table_args__ = (UniqueConstraint("subagent_id", "name", name="uq_subagent_prompt"),)

    def get_variables(self) -> Dict[str, str]:
        """Parse variables from JSON."""
        return json.loads(self.variables) if self.variables else {}

    def set_variables(self, variables: Dict[str, str]) -> None:
        """Serialize variables to JSON."""
        self.variables = json.dumps(variables)


class InterfaceModel(Base):
    """SQLAlchemy model for Interface specifications."""

    __tablename__ = "interfaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    protocol = Column(String(100), nullable=False)
    tools = Column(Text, default="[]")  # JSON array
    structured_outputs = Column(Text, default="[]")  # JSON array
    capabilities = Column(Text, default="[]")  # JSON array
    metadata = Column(Text, default="{}")  # JSON object

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="interfaces")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Parse tools from JSON."""
        return json.loads(self.tools) if self.tools else []

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Serialize tools to JSON."""
        self.tools = json.dumps(tools)

    def get_structured_outputs(self) -> List[Dict[str, Any]]:
        """Parse structured_outputs from JSON."""
        return json.loads(self.structured_outputs) if self.structured_outputs else []

    def set_structured_outputs(self, outputs: List[Dict[str, Any]]) -> None:
        """Serialize structured_outputs to JSON."""
        self.structured_outputs = json.dumps(outputs)

    def get_capabilities(self) -> List[str]:
        """Parse capabilities from JSON."""
        return json.loads(self.capabilities) if self.capabilities else []

    def set_capabilities(self, capabilities: List[str]) -> None:
        """Serialize capabilities to JSON."""
        self.capabilities = json.dumps(capabilities)

    def get_metadata(self) -> Dict[str, Any]:
        """Parse metadata from JSON."""
        return json.loads(self.metadata) if self.metadata else {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Serialize metadata to JSON."""
        self.metadata = json.dumps(metadata)


class InstallationModel(Base):
    """SQLAlchemy model for Installation methods."""

    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    method = Column(String(50), nullable=False)

    # Git fields
    repository = Column(String(512), nullable=True)
    branch = Column(String(255), nullable=True)
    commit = Column(String(255), nullable=True)

    # Package manager fields
    package_name = Column(String(255), nullable=True)
    package_version = Column(String(100), nullable=True)
    registry_url = Column(String(512), nullable=True)

    # Docker fields
    image = Column(String(512), nullable=True)

    # Remote API fields
    url = Column(String(512), nullable=True)
    auth = Column(Text, default="{}")  # JSON object

    # Post-install
    post_install_commands = Column(Text, default="[]")  # JSON array

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="installations")

    def get_auth(self) -> Dict[str, str]:
        """Parse auth from JSON."""
        return json.loads(self.auth) if self.auth else {}

    def set_auth(self, auth: Dict[str, str]) -> None:
        """Serialize auth to JSON."""
        self.auth = json.dumps(auth)

    def get_post_install_commands(self) -> List[str]:
        """Parse post_install_commands from JSON."""
        return json.loads(self.post_install_commands) if self.post_install_commands else []

    def set_post_install_commands(self, commands: List[str]) -> None:
        """Serialize post_install_commands to JSON."""
        self.post_install_commands = json.dumps(commands)


class ActivationModel(Base):
    """SQLAlchemy model for Activation configurations."""

    __tablename__ = "activations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    activation_type = Column(String(50), nullable=False)

    # Command execution
    command = Column(String(512), nullable=True)
    args = Column(Text, default="[]")  # JSON array
    working_dir = Column(String(512), nullable=True)

    # Environment variables
    env_vars = Column(Text, default="{}")  # JSON object

    # Health check
    health_check = Column(Text, default="{}")  # JSON object

    # Protocol-specific
    protocol = Column(String(100), nullable=True)
    capabilities = Column(Text, default="[]")  # JSON array

    # Connection info
    url = Column(String(512), nullable=True)
    auth = Column(Text, default="{}")  # JSON object

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="activations")

    def get_args(self) -> List[str]:
        """Parse args from JSON."""
        return json.loads(self.args) if self.args else []

    def set_args(self, args: List[str]) -> None:
        """Serialize args to JSON."""
        self.args = json.dumps(args)

    def get_env_vars(self) -> Dict[str, Any]:
        """Parse env_vars from JSON."""
        return json.loads(self.env_vars) if self.env_vars else {}

    def set_env_vars(self, env_vars: Dict[str, Any]) -> None:
        """Serialize env_vars to JSON."""
        self.env_vars = json.dumps(env_vars)

    def get_health_check(self) -> Dict[str, Any]:
        """Parse health_check from JSON."""
        return json.loads(self.health_check) if self.health_check else {}

    def set_health_check(self, health_check: Dict[str, Any]) -> None:
        """Serialize health_check to JSON."""
        self.health_check = json.dumps(health_check)

    def get_capabilities(self) -> List[str]:
        """Parse capabilities from JSON."""
        return json.loads(self.capabilities) if self.capabilities else []

    def set_capabilities(self, capabilities: List[str]) -> None:
        """Serialize capabilities to JSON."""
        self.capabilities = json.dumps(capabilities)

    def get_auth(self) -> Dict[str, str]:
        """Parse auth from JSON."""
        return json.loads(self.auth) if self.auth else {}

    def set_auth(self, auth: Dict[str, str]) -> None:
        """Serialize auth to JSON."""
        self.auth = json.dumps(auth)


class ExampleModel(Base):
    """SQLAlchemy model for Usage examples."""

    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subagent_id = Column(Integer, ForeignKey("subagents.id"), nullable=False)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subagent = relationship("SubAgentModel", back_populates="examples")


class DependencyModel(Base):
    """SQLAlchemy model for Dependencies."""

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
