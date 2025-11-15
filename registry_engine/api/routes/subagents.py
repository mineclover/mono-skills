"""SubAgents API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session, get_subagent_db
from registry_engine.database import SubAgentDB
from registry_engine.models import SubAgentCreate, SubAgentResponse

router = APIRouter()


@router.get("/", response_model=List[SubAgentResponse])
async def list_subagents(
    domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """List all subagents with optional filtering.

    Args:
        domain: Filter by domain (optional)
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        session: Database session

    Returns:
        List of SubAgent responses
    """
    subagent_db = SubAgentDB(session)
    subagents = subagent_db.list(domain=domain, skip=skip, limit=limit)
    return [subagent_db.to_response(s) for s in subagents]


@router.get("/{name}", response_model=SubAgentResponse)
async def get_subagent(
    name: str,
    session: Session = Depends(get_session),
):
    """Get detailed information about a specific subagent.

    Args:
        name: SubAgent name
        session: Database session

    Returns:
        SubAgent response

    Raises:
        HTTPException: If subagent not found
    """
    subagent_db = SubAgentDB(session)
    subagent = subagent_db.get_by_name(name)

    if not subagent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SubAgent '{name}' not found",
        )

    return subagent_db.to_response(subagent)


@router.post("/", response_model=SubAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_subagent(
    subagent_data: SubAgentCreate,
    session: Session = Depends(get_session),
):
    """Create a new subagent.

    Args:
        subagent_data: SubAgent data to create
        session: Database session

    Returns:
        Created SubAgent response

    Raises:
        HTTPException: If subagent already exists
    """
    subagent_db = SubAgentDB(session)

    # Check if already exists
    existing = subagent_db.get_by_name(subagent_data.metadata.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SubAgent '{subagent_data.metadata.name}' already exists",
        )

    subagent = subagent_db.create(subagent_data)
    return subagent_db.to_response(subagent)


@router.put("/{name}", response_model=SubAgentResponse)
async def update_subagent(
    name: str,
    subagent_data: SubAgentCreate,
    session: Session = Depends(get_session),
):
    """Update an existing subagent.

    Args:
        name: SubAgent name
        subagent_data: New SubAgent data
        session: Database session

    Returns:
        Updated SubAgent response

    Raises:
        HTTPException: If subagent not found
    """
    subagent_db = SubAgentDB(session)
    subagent = subagent_db.update(name, subagent_data)

    if not subagent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SubAgent '{name}' not found",
        )

    return subagent_db.to_response(subagent)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subagent(
    name: str,
    session: Session = Depends(get_session),
):
    """Delete a subagent.

    Args:
        name: SubAgent name
        session: Database session

    Raises:
        HTTPException: If subagent not found
    """
    subagent_db = SubAgentDB(session)
    deleted = subagent_db.delete(name)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SubAgent '{name}' not found",
        )
