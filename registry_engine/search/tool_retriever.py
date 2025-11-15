"""Tool retriever for RAG-based search."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from registry_engine.database.qdrant import QdrantDB
from registry_engine.database.tool_db import ToolDB


class ToolSearchResult(Dict[str, Any]):
    """Search result with score and metadata."""

    pass


class ToolRetriever:
    """Retrieves tools using RAG-based semantic search."""

    def __init__(self, qdrant_db: QdrantDB, session: Session):
        """Initialize retriever.

        Args:
            qdrant_db: Qdrant database client
            session: SQLite database session
        """
        self.qdrant = qdrant_db
        self.tool_db = ToolDB(session)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ToolSearchResult]:
        """Search for tools using semantic search.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            category: Filter by category (optional)
            tags: Filter by tags (optional)

        Returns:
            List of search results with scores and full metadata
        """
        # Search in vector DB
        vector_results = self.qdrant.search_tools(
            query=query,
            top_k=top_k,
            category=category,
            tags=tags,
        )

        # Enrich with full metadata from SQLite
        results = []
        for vr in vector_results:
            tool = self.tool_db.get_by_id(vr["id"])
            if tool:
                result = ToolSearchResult(
                    {
                        "name": tool.name,
                        "display_name": tool.display_name,
                        "description": tool.description,
                        "category": tool.category,
                        "tags": tool.get_tags(),
                        "score": vr["score"],
                        "subagent_name": tool.subagent.name,
                        "subagent_version": tool.subagent_version,
                        "protocol": tool.protocol,
                    }
                )
                results.append(result)

        return results

    def search_by_category(
        self, category: str, top_k: int = 10
    ) -> List[ToolSearchResult]:
        """Search for tools by category.

        Args:
            category: Category to search for
            top_k: Number of results to return

        Returns:
            List of search results
        """
        return self.search(query=f"tools in {category} category", top_k=top_k, category=category)
