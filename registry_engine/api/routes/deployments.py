"""API endpoints for managing deployments and runtime integrations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.deployment_db import DeploymentDB
from ...models.deployment import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentSearchRequest,
    DeploymentSearchResponse,
    HealthCheckRequest,
)

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("/", response_model=DeploymentResponse, status_code=201)
async def register_deployment(
    deployment: DeploymentCreate,
    session: Session = Depends(get_db),
):
    """
    Register a new deployment of a tool/agent.

    This allows you to register running instances of tools (e.g., Agno agents)
    so that users can discover and use them directly.

    Example:
        ```json
        {
          "tool_name": "web_search",
          "subagent_name": "tavily-search-toolkit",
          "deployment_name": "production-web-search",
          "environment": "production",
          "endpoint": {
            "url": "https://api.example.com/agents/web-search",
            "method": "POST",
            "auth_type": "bearer"
          },
          "metadata": {
            "platform": "agno",
            "platform_version": "1.0.0",
            "deployed_by": "devops-team"
          }
        }
        ```
    """
    db = DeploymentDB(session)

    # Verify tool exists
    from ...database.tool_db import ToolDB
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(deployment.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{deployment.tool_name}' not found")

    # Create deployment
    db_deployment = db.create_deployment(deployment)

    return db.to_response(db_deployment)


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    session: Session = Depends(get_db),
):
    """Get deployment information by ID."""
    db = DeploymentDB(session)
    deployment = db.get_deployment(deployment_id)

    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    return db.to_response(deployment)


@router.post("/search", response_model=DeploymentSearchResponse)
async def search_deployments(
    search: DeploymentSearchRequest,
    session: Session = Depends(get_db),
):
    """
    Search for deployments with filters.

    Allows filtering by:
    - tool_name
    - subagent_name
    - platform (agno, langserve, custom, etc.)
    - environment (production, staging, development)
    - status (running, stopped, error, deploying)
    - region

    Example:
        ```json
        {
          "platform": "agno",
          "environment": "production",
          "status": "running",
          "limit": 20
        }
        ```
    """
    db = DeploymentDB(session)
    results, total = db.search_deployments(search)

    return DeploymentSearchResponse(
        results=[db.to_response(d) for d in results],
        total=total,
        limit=search.limit,
        offset=search.offset,
    )


@router.get("/by-tool/{tool_name}", response_model=List[DeploymentResponse])
async def get_deployments_by_tool(
    tool_name: str,
    environment: Optional[str] = Query(None, description="Filter by environment"),
    session: Session = Depends(get_db),
):
    """Get all deployments for a specific tool."""
    db = DeploymentDB(session)
    deployments = db.get_deployments_by_tool(tool_name, environment)

    return [db.to_response(d) for d in deployments]


@router.patch("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    update: DeploymentUpdate,
    session: Session = Depends(get_db),
):
    """Update deployment information."""
    db = DeploymentDB(session)
    deployment = db.update_deployment(deployment_id, update)

    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    return db.to_response(deployment)


@router.post("/{deployment_id}/health", response_model=DeploymentResponse)
async def update_health_status(
    deployment_id: str,
    health: HealthCheckRequest,
    session: Session = Depends(get_db),
):
    """
    Update health status for a deployment.

    Platforms like Agno can call this endpoint periodically to report
    the health status of running agents.

    Example:
        ```json
        {
          "status": "running",
          "uptime_seconds": 86400,
          "request_count": 1523,
          "avg_latency_ms": 245.3
        }
        ```
    """
    db = DeploymentDB(session)
    deployment = db.update_health_status(deployment_id, health)

    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    return db.to_response(deployment)


@router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    session: Session = Depends(get_db),
):
    """Unregister a deployment."""
    db = DeploymentDB(session)
    success = db.delete_deployment(deployment_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")


@router.get("/{deployment_id}/health/history")
async def get_health_history(
    deployment_id: str,
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_db),
):
    """Get health check history for a deployment."""
    db = DeploymentDB(session)

    # Verify deployment exists
    deployment = db.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    history = db.get_health_history(deployment_id, limit)

    return {
        "deployment_id": deployment_id,
        "history": [
            {
                "status": log.status,
                "checked_at": log.checked_at,
                "response_time_ms": log.response_time_ms,
                "error_message": log.error_message,
                "uptime_seconds": log.uptime_seconds,
                "request_count": log.request_count,
                "avg_latency_ms": log.avg_latency_ms,
            }
            for log in history
        ],
        "total": len(history),
    }
