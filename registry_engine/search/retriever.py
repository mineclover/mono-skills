"""SubAgent retriever for RAG-based search."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from registry_engine.database.qdrant import QdrantDB
from registry_engine.database.sqlite import SubAgentDB


class SearchResult(Dict[str, Any]):
    """Search result with score and metadata."""

    pass


class SubAgentRetriever:
    """Retrieves subagents using RAG-based semantic search."""

    def __init__(self, qdrant_db: QdrantDB, session: Session):
        """Initialize retriever.

        Args:
            qdrant_db: Qdrant database client
            session: SQLite database session
        """
        self.qdrant = qdrant_db
        self.subagent_db = SubAgentDB(session)

    def search(
        self,
        query: str,
        top_k: int = 5,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Search for subagents using semantic search.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            domain: Filter by domain (optional)
            tags: Filter by tags (optional)

        Returns:
            List of search results with scores and full metadata
        """
        # Search in vector DB
        vector_results = self.qdrant.search(
            query=query,
            top_k=top_k,
            domain=domain,
            tags=tags,
        )

        # Enrich with full metadata from SQLite
        results = []
        for vr in vector_results:
            subagent = self.subagent_db.get_by_id(vr["id"])
            if subagent:
                result = SearchResult(
                    {
                        "name": subagent.name,
                        "version": subagent.version,
                        "description": subagent.description,
                        "domain": subagent.domain,
                        "tags": subagent.get_tags(),
                        "capabilities": subagent.get_capabilities(),
                        "use_cases": subagent.get_use_cases(),
                        "score": vr["score"],
                        "author": subagent.author,
                        "priority": subagent.priority,
                    }
                )
                results.append(result)

        # Re-rank by score and priority
        results = self._rerank(results)

        return results

    def search_by_capability(
        self, capability: str, top_k: int = 5
    ) -> List[SearchResult]:
        """Search for subagents by specific capability.

        Args:
            capability: Capability to search for
            top_k: Number of results to return

        Returns:
            List of search results
        """
        query = f"I need a subagent that can {capability}"
        return self.search(query=query, top_k=top_k)

    def _rerank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Re-rank results by combining score and priority.

        Args:
            results: Initial search results

        Returns:
            Re-ranked results
        """
        # Combine score (0-1) with priority (0-100) normalized to (0-1)
        for result in results:
            semantic_score = result["score"]
            priority_score = result.get("priority", 0) / 100.0

            # Weighted combination: 80% semantic, 20% priority
            combined_score = (0.8 * semantic_score) + (0.2 * priority_score)
            result["combined_score"] = combined_score

        # Sort by combined score
        results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        return results
