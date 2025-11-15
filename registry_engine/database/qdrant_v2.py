"""Qdrant vector database operations - Tool-focused."""

import os
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantDB:
    """Qdrant vector database client for Tools."""

    COLLECTION_NAME = "tools"
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

    def index_tool(
        self,
        tool_id: int,
        name: str,
        display_name: str,
        description: str,
        category: str,
        tags: List[str],
        subagent_name: str,
    ) -> None:
        """Index a tool in Qdrant.

        Args:
            tool_id: Tool database ID
            name: Tool name
            display_name: Display name
            description: Tool description
            category: Category
            tags: List of tags
            subagent_name: Parent SubAgent name
        """
        # Create text to embed
        text_to_embed = self._create_embedding_text(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            tags=tags,
        )

        # Generate embedding
        embedding = self.embeddings.embed_query(text_to_embed)

        # Create point
        point = PointStruct(
            id=tool_id,
            vector=embedding,
            payload={
                "name": name,
                "display_name": display_name,
                "description": description,
                "category": category,
                "tags": tags,
                "subagent_name": subagent_name,
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
        display_name: str,
        description: str,
        category: str,
        tags: List[str],
    ) -> str:
        """Create text for embedding.

        Args:
            name: Tool name
            display_name: Display name
            description: Description
            category: Category
            tags: Tags

        Returns:
            Combined text for embedding
        """
        parts = [
            f"Tool: {display_name}",
            f"Name: {name}",
            f"Description: {description}",
            f"Category: {category}",
        ]

        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        return "\n".join(parts)

    def search_tools(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for tools using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return
            category: Filter by category (optional)
            tags: Filter by tags (optional)

        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Build filter
        query_filter = None
        if category or tags:
            conditions = []

            if category:
                conditions.append({"key": "category", "match": {"value": category}})

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
                "display_name": result.payload["display_name"],
                "description": result.payload["description"],
                "category": result.payload["category"],
                "tags": result.payload["tags"],
                "subagent_name": result.payload["subagent_name"],
            }
            for result in results
        ]

    def delete_tool(self, tool_id: int) -> None:
        """Delete a tool from the index.

        Args:
            tool_id: Tool database ID
        """
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=[tool_id],
        )

    def reindex_all_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Reindex all tools.

        Args:
            tools: List of tool data to index
        """
        # Delete collection
        self.client.delete_collection(self.COLLECTION_NAME)

        # Recreate collection
        self._ensure_collection()

        # Index all tools
        for tool in tools:
            self.index_tool(
                tool_id=tool["id"],
                name=tool["name"],
                display_name=tool["display_name"],
                description=tool["description"],
                category=tool["category"],
                tags=tool.get("tags", []),
                subagent_name=tool["subagent_name"],
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
