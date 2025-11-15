"""SQLAlchemy models for deployments."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Import Base from models_v2 to ensure compatibility
try:
    from .models_v2 import Base
except ImportError:
    Base = declarative_base()


class DeploymentModel(Base):
    """Deployed instance of a tool/agent."""

    __tablename__ = "deployments"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String, unique=True, nullable=False, index=True)

    # References
    tool_name = Column(String, ForeignKey("tools.name"), nullable=False, index=True)
    subagent_name = Column(String, ForeignKey("subagents.name"), nullable=False, index=True)

    # Deployment info
    deployment_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Endpoint configuration (JSON)
    endpoint = Column(JSON, nullable=False)  # AgentEndpoint serialized

    # Deployment metadata (JSON)
    metadata = Column(JSON, nullable=False)  # DeploymentMetadata serialized

    # Status (JSON)
    status = Column(JSON, nullable=False)  # DeploymentStatus serialized

    # Environment
    environment = Column(String, nullable=False, default="development", index=True)
    region = Column(String, nullable=True)

    # Resource limits
    max_concurrent_requests = Column(Integer, nullable=True)
    rate_limit_per_minute = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tool = relationship("ToolModel", back_populates="deployments")
    subagent = relationship("SubAgentModel", back_populates="deployments")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_deployment_tool_env", "tool_name", "environment"),
        Index("idx_deployment_platform", "metadata"),  # For platform searches
        Index("idx_deployment_status", "status"),
    )


class DeploymentHealthLog(Base):
    """Health check history for deployments."""

    __tablename__ = "deployment_health_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String, ForeignKey("deployments.deployment_id"), nullable=False, index=True)

    # Health check results
    status = Column(String, nullable=False)  # running, stopped, error, etc.
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)

    # Metrics
    uptime_seconds = Column(Integer, nullable=True)
    request_count = Column(Integer, nullable=True)
    avg_latency_ms = Column(Integer, nullable=True)

    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Index for time-series queries
    __table_args__ = (
        Index("idx_health_deployment_time", "deployment_id", "checked_at"),
    )


class PlatformIntegration(Base):
    """Integration configuration for execution platforms (Agno, etc.)."""

    __tablename__ = "platform_integrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_name = Column(String, unique=True, nullable=False, index=True)

    # Configuration
    platform_type = Column(String, nullable=False)  # agno, langserve, custom, etc.
    api_url = Column(String, nullable=False)
    api_key_encrypted = Column(String, nullable=True)  # Encrypted API key

    # Integration settings
    auto_register_deployments = Column(Integer, default=1)  # Boolean as integer
    health_check_interval_seconds = Column(Integer, default=60)
    sync_agent_metadata = Column(Integer, default=1)  # Boolean as integer

    # Additional config (JSON)
    config = Column(JSON, nullable=True)

    # Status
    enabled = Column(Integer, default=1, index=True)  # Boolean as integer
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
