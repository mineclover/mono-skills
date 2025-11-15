"""Search API endpoints - Tool-focused."""

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session
from registry_engine.database.qdrant_v2 import QdrantDB
from registry_engine.search.tool_retriever import ToolRetriever

router = APIRouter()


class ToolSearchRequest(BaseModel):
    """Search request model for tools."""

    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class ToolSearchResponse(BaseModel):
    """Search response model."""

    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")


# Global Qdrant instance (initialized on first use)
_qdrant_db: Optional[QdrantDB] = None


def get_qdrant_db() -> QdrantDB:
    """Get or create Qdrant database instance.

    Returns:
        QdrantDB instance
    """
    global _qdrant_db
    if _qdrant_db is None:
        # Check for Qdrant URL in environment
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url:
            _qdrant_db = QdrantDB(url=qdrant_url, api_key=qdrant_api_key)
        else:
            # Use in-memory mode for development
            _qdrant_db = QdrantDB(use_memory=True)

    return _qdrant_db


@router.post("/tools", response_model=ToolSearchResponse)
async def search_tools(
    request: ToolSearchRequest,
    session: Session = Depends(get_session),
):
    """Search for tools using natural language.

    Args:
        request: Search request
        session: Database session

    Returns:
        Search results with scores
    """
    start_time = time.time()

    # Get retriever
    qdrant_db = get_qdrant_db()
    retriever = ToolRetriever(qdrant_db, session)

    # Search
    results = retriever.search(
        query=request.query,
        top_k=request.top_k,
        category=request.category,
        tags=request.tags,
    )

    query_time_ms = (time.time() - start_time) * 1000

    return ToolSearchResponse(
        results=results,
        total=len(results),
        query_time_ms=query_time_ms,
    )


@router.get("/tools/by-category", response_model=ToolSearchResponse)
async def search_by_category(
    category: str = Query(..., description="Category to search for"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of results"),
    session: Session = Depends(get_session),
):
    """Search tools by category.

    Args:
        category: Category name
        top_k: Number of results to return
        session: Database session

    Returns:
        Search results
    """
    start_time = time.time()

    # Get retriever
    qdrant_db = get_qdrant_db()
    retriever = ToolRetriever(qdrant_db, session)

    # Search
    results = retriever.search_by_category(category=category, top_k=top_k)

    query_time_ms = (time.time() - start_time) * 1000

    return ToolSearchResponse(
        results=results,
        total=len(results),
        query_time_ms=query_time_ms,
    )
