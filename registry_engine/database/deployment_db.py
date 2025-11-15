"""CRUD operations for deployments."""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .deployment_models import DeploymentModel, DeploymentHealthLog, PlatformIntegration
from ..models.deployment import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentSearchRequest,
    DeploymentStatus,
    HealthCheckRequest,
)


class DeploymentDB:
    """Database operations for deployments."""

    def __init__(self, session: Session):
        self.session = session

    def create_deployment(self, deployment: DeploymentCreate) -> DeploymentModel:
        """Create a new deployment."""
        deployment_id = f"deploy_{uuid.uuid4().hex[:16]}"

        db_deployment = DeploymentModel(
            deployment_id=deployment_id,
            tool_name=deployment.tool_name,
            subagent_name=deployment.subagent_name,
            deployment_name=deployment.deployment_name,
            description=deployment.description,
            endpoint=deployment.endpoint.dict(),
            metadata=deployment.metadata.dict(),
            status={
                "status": "deploying",
                "last_health_check": None,
                "error_message": None,
            },
            environment=deployment.environment,
            region=deployment.region,
            max_concurrent_requests=deployment.max_concurrent_requests,
            rate_limit_per_minute=deployment.rate_limit_per_minute,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(db_deployment)
        self.session.commit()
        self.session.refresh(db_deployment)

        return db_deployment

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentModel]:
        """Get deployment by ID."""
        return (
            self.session.query(DeploymentModel)
            .filter(DeploymentModel.deployment_id == deployment_id)
            .first()
        )

    def get_deployments_by_tool(
        self, tool_name: str, environment: Optional[str] = None
    ) -> List[DeploymentModel]:
        """Get all deployments for a tool."""
        query = self.session.query(DeploymentModel).filter(
            DeploymentModel.tool_name == tool_name
        )

        if environment:
            query = query.filter(DeploymentModel.environment == environment)

        return query.all()

    def search_deployments(
        self, search: DeploymentSearchRequest
    ) -> tuple[List[DeploymentModel], int]:
        """Search deployments with filters."""
        query = self.session.query(DeploymentModel)

        # Apply filters
        if search.tool_name:
            query = query.filter(DeploymentModel.tool_name == search.tool_name)

        if search.subagent_name:
            query = query.filter(DeploymentModel.subagent_name == search.subagent_name)

        if search.environment:
            query = query.filter(DeploymentModel.environment == search.environment)

        if search.region:
            query = query.filter(DeploymentModel.region == search.region)

        if search.platform:
            # JSON search for platform
            query = query.filter(
                DeploymentModel.metadata["platform"].astext == search.platform
            )

        if search.status:
            # JSON search for status
            query = query.filter(
                DeploymentModel.status["status"].astext == search.status
            )

        # Get total count
        total = query.count()

        # Apply pagination
        results = query.offset(search.offset).limit(search.limit).all()

        return results, total

    def update_deployment(
        self, deployment_id: str, update: DeploymentUpdate
    ) -> Optional[DeploymentModel]:
        """Update deployment information."""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        if update.description is not None:
            deployment.description = update.description

        if update.endpoint is not None:
            deployment.endpoint = update.endpoint.dict()

        if update.status is not None:
            deployment.status = update.status.dict()

        if update.environment is not None:
            deployment.environment = update.environment

        if update.max_concurrent_requests is not None:
            deployment.max_concurrent_requests = update.max_concurrent_requests

        if update.rate_limit_per_minute is not None:
            deployment.rate_limit_per_minute = update.rate_limit_per_minute

        deployment.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(deployment)

        return deployment

    def update_health_status(
        self, deployment_id: str, health: HealthCheckRequest
    ) -> Optional[DeploymentModel]:
        """Update deployment health status."""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        # Update status
        status_dict = json.loads(json.dumps(deployment.status)) if isinstance(deployment.status, str) else deployment.status
        status_dict.update({
            "status": health.status,
            "last_health_check": datetime.utcnow().isoformat(),
            "error_message": health.error_message,
            "uptime_seconds": health.uptime_seconds,
            "request_count": health.request_count,
            "avg_latency_ms": health.avg_latency_ms,
        })
        deployment.status = status_dict
        deployment.updated_at = datetime.utcnow()

        # Log health check
        health_log = DeploymentHealthLog(
            deployment_id=deployment_id,
            status=health.status,
            error_message=health.error_message,
            uptime_seconds=health.uptime_seconds,
            request_count=health.request_count,
            avg_latency_ms=health.avg_latency_ms,
            checked_at=datetime.utcnow(),
        )
        self.session.add(health_log)

        self.session.commit()
        self.session.refresh(deployment)

        return deployment

    def delete_deployment(self, deployment_id: str) -> bool:
        """Delete a deployment."""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return False

        self.session.delete(deployment)
        self.session.commit()

        return True

    def to_response(self, deployment: DeploymentModel) -> DeploymentResponse:
        """Convert database model to response model."""
        from ..models.deployment import AgentEndpoint, DeploymentMetadata, DeploymentStatus

        # Get tool info for aggregation
        tool_display_name = None
        tool_category = None
        if deployment.tool:
            tool_display_name = deployment.tool.display_name
            tool_category = deployment.tool.category

        endpoint_dict = deployment.endpoint if isinstance(deployment.endpoint, dict) else json.loads(deployment.endpoint)
        metadata_dict = deployment.metadata if isinstance(deployment.metadata, dict) else json.loads(deployment.metadata)
        status_dict = deployment.status if isinstance(deployment.status, dict) else json.loads(deployment.status)

        return DeploymentResponse(
            deployment_id=deployment.deployment_id,
            tool_name=deployment.tool_name,
            subagent_name=deployment.subagent_name,
            deployment_name=deployment.deployment_name,
            description=deployment.description,
            endpoint=AgentEndpoint(**endpoint_dict),
            metadata=DeploymentMetadata(**metadata_dict),
            status=DeploymentStatus(**status_dict),
            environment=deployment.environment,
            region=deployment.region,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
            tool_display_name=tool_display_name,
            tool_category=tool_category,
        )

    def get_health_history(
        self, deployment_id: str, limit: int = 100
    ) -> List[DeploymentHealthLog]:
        """Get health check history for a deployment."""
        return (
            self.session.query(DeploymentHealthLog)
            .filter(DeploymentHealthLog.deployment_id == deployment_id)
            .order_by(DeploymentHealthLog.checked_at.desc())
            .limit(limit)
            .all()
        )

    # Platform integration methods
    def create_platform_integration(
        self, platform_name: str, platform_type: str, api_url: str, config: Optional[Dict] = None
    ) -> PlatformIntegration:
        """Create a platform integration configuration."""
        integration = PlatformIntegration(
            platform_name=platform_name,
            platform_type=platform_type,
            api_url=api_url,
            config=config or {},
            enabled=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(integration)
        self.session.commit()
        self.session.refresh(integration)

        return integration

    def get_platform_integration(self, platform_name: str) -> Optional[PlatformIntegration]:
        """Get platform integration by name."""
        return (
            self.session.query(PlatformIntegration)
            .filter(PlatformIntegration.platform_name == platform_name)
            .first()
        )

    def list_platform_integrations(self, enabled_only: bool = True) -> List[PlatformIntegration]:
        """List all platform integrations."""
        query = self.session.query(PlatformIntegration)

        if enabled_only:
            query = query.filter(PlatformIntegration.enabled == 1)

        return query.all()
