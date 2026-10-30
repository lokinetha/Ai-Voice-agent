"""
KnowledgeRetrievalPort Interface for Agent Runtime.

Abstract port for retrieving relevant knowledge context snippets.
Rule: Failure during knowledge retrieval must not corrupt Conversation state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class KnowledgeRetrievalPort(ABC):
    """Abstract port for Knowledge context retrieval."""

    @abstractmethod
    async def retrieve_knowledge(
        self, workspace_id: str, query: str, top_k: int = 3
    ) -> list[str]:
        """Retrieve relevant knowledge snippets for query.

        Args:
            workspace_id: Owning Workspace ID.
            query: User query/message string.
            top_k: Maximum number of relevant snippets to retrieve.

        Returns:
            List of retrieved text snippets.
        """
        ...
