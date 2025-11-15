"""Advanced search API with metadata filtering and facets."""

import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session
from registry_engine.database.models_v2 import ToolModel, SubAgentModel
from registry_engine.database.qdrant_v2 import QdrantDB
from registry_engine.database.tool_db import ToolDB
from registry_engine.search.tool_retriever import ToolRetriever
from registry_engine.api.routes.search_v2 import get_qdrant_db

router = APIRouter()


class AdvancedSearchRequest(BaseModel):
    """Advanced search request with multiple filters."""

    # Text search
    query: Optional[str] = Field(None, description="Natural language search query")

    # Filters
    categories: Optional[List[str]] = Field(None, description="Filter by categories (OR)")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (AND)")
    protocols: Optional[List[str]] = Field(None, description="Filter by protocols")
    subagent_names: Optional[List[str]] = Field(None, description="Filter by SubAgent names")

    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of results to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results to return")

    # Sorting
    sort_by: Literal["relevance", "name", "created_at", "category"] = Field(
        default="relevance", description="Sort order"
    )
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort direction")


class FacetValue(BaseModel):
    """A facet value with count."""

    value: str
    count: int


class SearchFacets(BaseModel):
    """Search facets for filtering."""

    categories: List[FacetValue] = Field(default_factory=list)
    tags: List[FacetValue] = Field(default_factory=list)
    protocols: List[FacetValue] = Field(default_factory=list)
    subagents: List[FacetValue] = Field(default_factory=list)


class AdvancedSearchResponse(BaseModel):
    """Advanced search response with facets."""

    results: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int
    facets: SearchFacets
    query_time_ms: float


@router.post("/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    session: Session = Depends(get_session),
):
    """Advanced search with multiple filters and facets.

    Combines semantic search (if query provided) with metadata filtering.

    Args:
        request: Search request with filters
        session: Database session

    Returns:
        Search results with facets
    """
    start_time = time.time()

    tool_db = ToolDB(session)

    # Build base query
    stmt = select(ToolModel).join(SubAgentModel)

    # Apply filters
    if request.categories:
        stmt = stmt.where(ToolModel.category.in_(request.categories))

    if request.protocols:
        stmt = stmt.where(ToolModel.protocol.in_(request.protocols))

    if request.subagent_names:
        stmt = stmt.where(SubAgentModel.name.in_(request.subagent_names))

    if request.tags:
        # Tags require JSON contains check - simplified version
        for tag in request.tags:
            stmt = stmt.where(ToolModel.tags.contains(f'"{tag}"'))

    # Get results before pagination for facets
    all_results = session.execute(stmt).scalars().all()

    # Apply sorting
    if request.sort_by == "name":
        all_results = sorted(all_results, key=lambda t: t.name, reverse=(request.sort_order == "desc"))
    elif request.sort_by == "created_at":
        all_results = sorted(all_results, key=lambda t: t.created_at, reverse=(request.sort_order == "desc"))
    elif request.sort_by == "category":
        all_results = sorted(all_results, key=lambda t: t.category, reverse=(request.sort_order == "desc"))
    elif request.sort_by == "relevance" and request.query:
        # Use semantic search for relevance sorting
        qdrant_db = get_qdrant_db()
        retriever = ToolRetriever(qdrant_db, session)
        semantic_results = retriever.search(
            query=request.query,
            top_k=len(all_results),
            category=request.categories[0] if request.categories and len(request.categories) == 1 else None,
            tags=request.tags,
        )
        # Create ID to score map
        score_map = {r["name"]: r["score"] for r in semantic_results}
        all_results = sorted(all_results, key=lambda t: score_map.get(t.name, 0), reverse=True)

    # Generate facets from all results
    facets = _generate_facets(all_results)

    # Apply pagination
    paginated_results = all_results[request.skip : request.skip + request.limit]

    # Convert to response format
    results = [tool_db.to_response(t).model_dump() for t in paginated_results]

    query_time_ms = (time.time() - start_time) * 1000

    return AdvancedSearchResponse(
        results=results,
        total=len(all_results),
        skip=request.skip,
        limit=request.limit,
        facets=facets,
        query_time_ms=query_time_ms,
    )


@router.get("/facets", response_model=SearchFacets)
async def get_facets(
    session: Session = Depends(get_session),
):
    """Get available facets for filtering.

    Returns all unique values for categories, tags, protocols, and subagents
    with their counts.

    Args:
        session: Database session

    Returns:
        Available facets
    """
    tools = session.query(ToolModel).join(SubAgentModel).all()
    return _generate_facets(tools)


@router.get("/suggest")
async def suggest_tools(
    q: str = Query(..., description="Partial query for autocomplete"),
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
):
    """Autocomplete/suggest tools based on partial query.

    Args:
        q: Partial query string
        limit: Max suggestions
        session: Database session

    Returns:
        Suggested tools
    """
    stmt = (
        select(ToolModel)
        .where(
            (ToolModel.name.contains(q))
            | (ToolModel.display_name.contains(q))
            | (ToolModel.description.contains(q))
        )
        .limit(limit)
    )

    tools = session.execute(stmt).scalars().all()

    return [
        {
            "name": t.name,
            "display_name": t.display_name,
            "category": t.category,
            "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
        }
        for t in tools
    ]


@router.get("/similar/{tool_name}")
async def find_similar_tools(
    tool_name: str,
    limit: int = Query(default=5, ge=1, le=20),
    session: Session = Depends(get_session),
):
    """Find similar tools based on a given tool.

    Uses the tool's description and category to find similar ones.

    Args:
        tool_name: Tool name to find similar tools for
        limit: Number of similar tools to return
        session: Database session

    Returns:
        Similar tools
    """
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(tool_name)

    if not tool:
        from fastapi import HTTPException, status as http_status

        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    # Use semantic search with the tool's description
    qdrant_db = get_qdrant_db()
    retriever = ToolRetriever(qdrant_db, session)

    # Search using description
    results = retriever.search(
        query=tool.description,
        top_k=limit + 1,  # +1 to exclude self
        category=tool.category,  # Same category
    )

    # Filter out the original tool
    similar = [r for r in results if r["name"] != tool_name][:limit]

    return similar


@router.get("/statistics")
async def get_statistics(
    session: Session = Depends(get_session),
):
    """Get registry statistics.

    Args:
        session: Database session

    Returns:
        Statistics about tools and subagents
    """
    total_tools = session.query(func.count(ToolModel.id)).scalar()
    total_subagents = session.query(func.count(SubAgentModel.id)).scalar()

    # Category distribution
    category_stats = (
        session.query(ToolModel.category, func.count(ToolModel.id))
        .group_by(ToolModel.category)
        .all()
    )

    # Protocol distribution
    protocol_stats = (
        session.query(ToolModel.protocol, func.count(ToolModel.id))
        .group_by(ToolModel.protocol)
        .all()
    )

    # Recent tools (last 30 days)
    from datetime import datetime, timedelta

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_tools = (
        session.query(func.count(ToolModel.id))
        .where(ToolModel.created_at >= thirty_days_ago)
        .scalar()
    )

    return {
        "total_tools": total_tools,
        "total_subagents": total_subagents,
        "recent_tools_30d": recent_tools,
        "categories": {cat: count for cat, count in category_stats},
        "protocols": {proto: count for proto, count in protocol_stats},
    }


def _generate_facets(tools: List[ToolModel]) -> SearchFacets:
    """Generate facets from a list of tools.

    Args:
        tools: List of tool models

    Returns:
        Facets with counts
    """
    from collections import Counter

    # Count categories
    category_counts = Counter(t.category for t in tools)
    categories = [
        FacetValue(value=cat, count=count) for cat, count in category_counts.most_common()
    ]

    # Count tags
    tag_counts = Counter()
    for tool in tools:
        for tag in tool.get_tags():
            tag_counts[tag] += 1
    tags = [FacetValue(value=tag, count=count) for tag, count in tag_counts.most_common(20)]

    # Count protocols
    protocol_counts = Counter(t.protocol for t in tools)
    protocols = [
        FacetValue(value=proto, count=count) for proto, count in protocol_counts.most_common()
    ]

    # Count subagents
    subagent_counts = Counter(t.subagent.name for t in tools)
    subagents = [
        FacetValue(value=name, count=count) for name, count in subagent_counts.most_common(20)
    ]

    return SearchFacets(
        categories=categories,
        tags=tags,
        protocols=protocols,
        subagents=subagents,
    )
