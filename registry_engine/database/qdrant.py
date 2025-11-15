"""Qdrant vector database operations."""

import os
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantDB:
    """Qdrant vector database client."""

    COLLECTION_NAME = "subagents"
    VECTOR_SIZE = 1536  # OpenAI ada-002 embedding size
    DISTANCE_METRIC = Distance.COSINE

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_memory: bool = False,
    ):
        """Initialize Qdrant client.

        Args:
            url: Qdrant server URL (default: in-memory)
            api_key: Qdrant API key (optional)
            use_memory: Use in-memory mode (default: False)
        """
        if use_memory or not url:
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(url=url, api_key=api_key)

        # Initialize embeddings
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("Warning: OPENAI_API_KEY not set. Embeddings will not work.")

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key,
        )

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the collection exists."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=self.DISTANCE_METRIC,
                ),
            )

    def index_subagent(
        self,
        subagent_id: int,
        name: str,
        description: str,
        domain: str,
        tags: List[str],
        capabilities: List[str],
        use_cases: List[str],
    ) -> None:
        """Index a subagent in Qdrant.

        Args:
            subagent_id: SubAgent database ID
            name: SubAgent name
            description: SubAgent description
            domain: Domain category
            tags: List of tags
            capabilities: List of capabilities
            use_cases: List of use cases
        """
        # Create text to embed
        text_to_embed = self._create_embedding_text(
            name=name,
            description=description,
            domain=domain,
            tags=tags,
            capabilities=capabilities,
            use_cases=use_cases,
        )

        # Generate embedding
        embedding = self.embeddings.embed_query(text_to_embed)

        # Create point
        point = PointStruct(
            id=subagent_id,
            vector=embedding,
            payload={
                "name": name,
                "description": description,
                "domain": domain,
                "tags": tags,
                "capabilities": capabilities,
                "use_cases": use_cases,
            },
        )

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point],
        )

    def _create_embedding_text(
        self,
        name: str,
        description: str,
        domain: str,
        tags: List[str],
        capabilities: List[str],
        use_cases: List[str],
    ) -> str:
        """Create text for embedding.

        Args:
            name: SubAgent name
            description: SubAgent description
            domain: Domain category
            tags: List of tags
            capabilities: List of capabilities
            use_cases: List of use cases

        Returns:
            Combined text for embedding
        """
        parts = [
            f"Name: {name}",
            f"Description: {description}",
            f"Domain: {domain}",
        ]

        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        if capabilities:
            parts.append(f"Capabilities: {' '.join(capabilities)}")

        if use_cases:
            parts.append(f"Use cases: {' '.join(use_cases)}")

        return "\n".join(parts)

    def search(
        self,
        query: str,
        top_k: int = 5,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for subagents using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return
            domain: Filter by domain (optional)
            tags: Filter by tags (optional)

        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Build filter
        query_filter = None
        if domain or tags:
            conditions = []

            if domain:
                conditions.append({"key": "domain", "match": {"value": domain}})

            if tags:
                for tag in tags:
                    conditions.append({"key": "tags", "match": {"any": [tag]}})

            if len(conditions) == 1:
                query_filter = {"must": conditions}
            else:
                query_filter = {"must": conditions}

        # Search
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter,
        )

        # Format results
        return [
            {
                "id": result.id,
                "score": result.score,
                "name": result.payload["name"],
                "description": result.payload["description"],
                "domain": result.payload["domain"],
                "tags": result.payload["tags"],
            }
            for result in results
        ]

    def delete_subagent(self, subagent_id: int) -> None:
        """Delete a subagent from the index.

        Args:
            subagent_id: SubAgent database ID
        """
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=[subagent_id],
        )

    def reindex_all(self, subagents: List[Dict[str, Any]]) -> None:
        """Reindex all subagents.

        Args:
            subagents: List of subagent data to index
        """
        # Delete collection
        self.client.delete_collection(self.COLLECTION_NAME)

        # Recreate collection
        self._ensure_collection()

        # Index all subagents
        for subagent in subagents:
            self.index_subagent(
                subagent_id=subagent["id"],
                name=subagent["name"],
                description=subagent["description"],
                domain=subagent["domain"],
                tags=subagent.get("tags", []),
                capabilities=subagent.get("capabilities", []),
                use_cases=subagent.get("use_cases", []),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Collection stats
        """
        collection_info = self.client.get_collection(self.COLLECTION_NAME)
        return {
            "collection_name": self.COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": collection_info.status,
        }
