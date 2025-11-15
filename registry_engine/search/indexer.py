"""SubAgent indexer for vector database."""

from typing import List

from sqlalchemy.orm import Session

from registry_engine.database.models import SubAgentModel
from registry_engine.database.qdrant import QdrantDB


class SubAgentIndexer:
    """Indexes subagents into Qdrant vector database."""

    def __init__(self, qdrant_db: QdrantDB):
        """Initialize indexer.

        Args:
            qdrant_db: Qdrant database client
        """
        self.qdrant = qdrant_db

    def index_subagent(self, subagent: SubAgentModel) -> None:
        """Index a single subagent.

        Args:
            subagent: SubAgent model to index
        """
        self.qdrant.index_subagent(
            subagent_id=subagent.id,
            name=subagent.name,
            description=subagent.description,
            domain=subagent.domain,
            tags=subagent.get_tags(),
            capabilities=subagent.get_capabilities(),
            use_cases=subagent.get_use_cases(),
        )

    def delete_subagent(self, subagent_id: int) -> None:
        """Delete a subagent from the index.

        Args:
            subagent_id: SubAgent database ID
        """
        self.qdrant.delete_subagent(subagent_id)

    def reindex_all(self, session: Session) -> int:
        """Reindex all subagents from the database.

        Args:
            session: Database session

        Returns:
            Number of subagents indexed
        """
        subagents = session.query(SubAgentModel).all()

        subagent_data = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "domain": s.domain,
                "tags": s.get_tags(),
                "capabilities": s.get_capabilities(),
                "use_cases": s.get_use_cases(),
            }
            for s in subagents
        ]

        self.qdrant.reindex_all(subagent_data)
        return len(subagents)
