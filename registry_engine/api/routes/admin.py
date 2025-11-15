"""Admin API endpoints."""

import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session
from registry_engine.api.routes.search import get_qdrant_db
from registry_engine.search.indexer import SubAgentIndexer

router = APIRouter()


class ReindexResponse(BaseModel):
    """Reindex response model."""

    message: str
    subagents_indexed: int


class StatsResponse(BaseModel):
    """Statistics response model."""

    subagents_count: int
    vector_db_stats: Dict[str, Any]


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_all(
    session: Session = Depends(get_session),
):
    """Rebuild the entire vector index.

    Args:
        session: Database session

    Returns:
        Reindex result
    """
    qdrant_db = get_qdrant_db()
    indexer = SubAgentIndexer(qdrant_db)

    count = indexer.reindex_all(session)

    return ReindexResponse(
        message="Reindexing completed successfully",
        subagents_indexed=count,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: Session = Depends(get_session),
):
    """Get registry statistics.

    Args:
        session: Database session

    Returns:
        Registry statistics
    """
    from registry_engine.database.models import SubAgentModel

    # Count subagents
    subagents_count = session.query(SubAgentModel).count()

    # Get vector DB stats
    qdrant_db = get_qdrant_db()
    vector_stats = qdrant_db.get_stats()

    return StatsResponse(
        subagents_count=subagents_count,
        vector_db_stats=vector_stats,
    )
