"""API endpoints that combine tool information with deployment status."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.connection import get_db
from ...database.tool_db import ToolDB
from ...database.deployment_db import DeploymentDB
from ...models.deployment import DeploymentResponse

router = APIRouter(prefix="/tools", tags=["tool-deployments"])


class ToolWithDeployments(BaseModel):
    """Tool information with available deployments."""

    # Tool info
    name: str
    display_name: str
    description: str
    category: str
    tags: List[str]
    subagent_name: str

    # Deployment info
    deployments: List[DeploymentResponse]
    total_deployments: int
    running_deployments: int
    production_deployments: int


class RunningToolsResponse(BaseModel):
    """Response for finding running tools."""

    results: List[ToolWithDeployments]
    total: int


@router.get("/{tool_name}/deployments", response_model=ToolWithDeployments)
async def get_tool_with_deployments(
    tool_name: str,
    environment: Optional[str] = Query(None, description="Filter deployments by environment"),
    status: Optional[str] = Query(None, description="Filter deployments by status"),
    session: Session = Depends(get_db),
):
    """
    Get tool information along with all available deployments.

    This helps users find running instances of a tool they want to use.

    Example use case:
    - User searches for "web search" tool
    - Gets tool metadata (how to install, prompts, etc.)
    - Also sees which production instances are already running
    - Can directly use running instance instead of installing locally
    """
    from fastapi import HTTPException

    tool_db = ToolDB(session)
    deployment_db = DeploymentDB(session)

    # Get tool info
    tool = tool_db.get_by_name(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # Get deployments
    deployments = deployment_db.get_deployments_by_tool(tool_name, environment)

    # Filter by status if provided
    if status:
        import json
        deployments = [
            d for d in deployments
            if (json.loads(json.dumps(d.status)) if isinstance(d.status, str) else d.status).get("status") == status
        ]

    # Calculate stats
    total_deployments = len(deployments)
    running_deployments = sum(
        1 for d in deployments
        if (d.status if isinstance(d.status, dict) else {}).get("status") == "running"
    )
    production_deployments = sum(
        1 for d in deployments
        if d.environment == "production"
    )

    tool_response = tool_db.to_response(tool)

    return ToolWithDeployments(
        name=tool_response.name,
        display_name=tool_response.display_name,
        description=tool_response.description,
        category=tool_response.category,
        tags=tool_response.tags,
        subagent_name=tool_response.subagent_name,
        deployments=[deployment_db.to_response(d) for d in deployments],
        total_deployments=total_deployments,
        running_deployments=running_deployments,
        production_deployments=production_deployments,
    )


@router.get("/running", response_model=RunningToolsResponse)
async def get_running_tools(
    environment: str = Query("production", description="Environment filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    """
    Get all tools that have running deployments.

    This is useful for discovering which tools are already deployed and
    ready to use without installation.

    Filters:
    - environment: production, staging, development (default: production)
    - category: search, security, image-processing, etc.
    - limit: max results to return
    """
    tool_db = ToolDB(session)
    deployment_db = DeploymentDB(session)

    # Search for deployments
    from ...models.deployment import DeploymentSearchRequest
    search_req = DeploymentSearchRequest(
        environment=environment,
        status="running",
        limit=1000,  # Get all running
    )

    deployments, total = deployment_db.search_deployments(search_req)

    # Group by tool
    tool_deployment_map = {}
    for deployment in deployments:
        tool_name = deployment.tool_name
        if tool_name not in tool_deployment_map:
            tool_deployment_map[tool_name] = []
        tool_deployment_map[tool_name].append(deployment)

    # Get tool info and build response
    results = []
    for tool_name, tool_deployments in tool_deployment_map.items():
        tool = tool_db.get_by_name(tool_name)
        if not tool:
            continue

        # Apply category filter
        if category and tool.category != category:
            continue

        tool_response = tool_db.to_response(tool)

        results.append(
            ToolWithDeployments(
                name=tool_response.name,
                display_name=tool_response.display_name,
                description=tool_response.description,
                category=tool_response.category,
                tags=tool_response.tags,
                subagent_name=tool_response.subagent_name,
                deployments=[deployment_db.to_response(d) for d in tool_deployments],
                total_deployments=len(tool_deployments),
                running_deployments=len(tool_deployments),  # All are running due to filter
                production_deployments=sum(
                    1 for d in tool_deployments if d.environment == "production"
                ),
            )
        )

    # Apply limit
    results = results[:limit]

    return RunningToolsResponse(
        results=results,
        total=len(results),
    )


@router.get("/by-platform/{platform}", response_model=RunningToolsResponse)
async def get_tools_by_platform(
    platform: str,
    environment: Optional[str] = Query(None, description="Environment filter"),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    """
    Get all tools deployed on a specific platform (e.g., Agno, LangServe).

    This helps users discover what tools are available on their preferred
    execution platform.

    Platforms:
    - agno
    - langserve
    - custom
    - docker
    - kubernetes
    - aws_lambda
    - gcp_cloud_run
    """
    tool_db = ToolDB(session)
    deployment_db = DeploymentDB(session)

    # Search for deployments on this platform
    from ...models.deployment import DeploymentSearchRequest
    search_req = DeploymentSearchRequest(
        platform=platform,
        environment=environment,
        status="running",
        limit=1000,
    )

    deployments, total = deployment_db.search_deployments(search_req)

    # Group by tool
    tool_deployment_map = {}
    for deployment in deployments:
        tool_name = deployment.tool_name
        if tool_name not in tool_deployment_map:
            tool_deployment_map[tool_name] = []
        tool_deployment_map[tool_name].append(deployment)

    # Build response
    results = []
    for tool_name, tool_deployments in tool_deployment_map.items():
        tool = tool_db.get_by_name(tool_name)
        if not tool:
            continue

        tool_response = tool_db.to_response(tool)

        results.append(
            ToolWithDeployments(
                name=tool_response.name,
                display_name=tool_response.display_name,
                description=tool_response.description,
                category=tool_response.category,
                tags=tool_response.tags,
                subagent_name=tool_response.subagent_name,
                deployments=[deployment_db.to_response(d) for d in tool_deployments],
                total_deployments=len(tool_deployments),
                running_deployments=len(tool_deployments),
                production_deployments=sum(
                    1 for d in tool_deployments if d.environment == "production"
                ),
            )
        )

    # Apply limit
    results = results[:limit]

    return RunningToolsResponse(
        results=results,
        total=len(results),
    )
