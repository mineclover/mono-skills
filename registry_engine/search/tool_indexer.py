"""Tool indexer for vector database."""

from typing import List

from sqlalchemy.orm import Session

from registry_engine.database.models_v2 import ToolModel
from registry_engine.database.qdrant import QdrantDB


class ToolIndexer:
    """Indexes tools into Qdrant vector database."""

    def __init__(self, qdrant_db: QdrantDB):
        """Initialize indexer.

        Args:
            qdrant_db: Qdrant database client
        """
        self.qdrant = qdrant_db

    def index_tool(self, tool: ToolModel) -> None:
        """Index a single tool.

        Args:
            tool: Tool model to index
        """
        self.qdrant.index_tool(
            tool_id=tool.id,
            name=tool.name,
            display_name=tool.display_name,
            description=tool.description,
            category=tool.category,
            tags=tool.get_tags(),
            subagent_name=tool.subagent.name,
        )

    def delete_tool(self, tool_id: int) -> None:
        """Delete a tool from the index.

        Args:
            tool_id: Tool database ID
        """
        self.qdrant.delete_tool(tool_id)

    def reindex_all(self, session: Session) -> int:
        """Reindex all tools from the database.

        Args:
            session: Database session

        Returns:
            Number of tools indexed
        """
        tools = session.query(ToolModel).all()

        tool_data = [
            {
                "id": t.id,
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category,
                "tags": t.get_tags(),
                "subagent_name": t.subagent.name,
            }
            for t in tools
        ]

        self.qdrant.reindex_all_tools(tool_data)
        return len(tools)
