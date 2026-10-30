"""
Chunk Entity for Knowledge Bounded Context.

Represents a text segment produced during document processing with embedding reference ID.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class Chunk(Entity[EntityId]):
    """Chunk Entity child owned by Document entity within KnowledgeBase aggregate."""

    def __init__(
        self,
        id: EntityId,
        text_content: str,
        sequence_index: int,
        token_count: int,
        embedding_id: str | None = None,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not text_content or not isinstance(text_content, str):
            raise ValueError("Chunk text_content cannot be empty")
        if sequence_index < 0:
            raise ValueError("sequence_index cannot be negative")
        if token_count < 0:
            raise ValueError("token_count cannot be negative")

        self._text_content = text_content
        self._sequence_index = sequence_index
        self._token_count = token_count
        self._embedding_id = embedding_id

    @property
    def text_content(self) -> str:
        return self._text_content

    @property
    def sequence_index(self) -> int:
        return self._sequence_index

    @property
    def token_count(self) -> int:
        return self._token_count

    @property
    def embedding_id(self) -> str | None:
        """Reference ID to vector store embedding (no vector calculations in Domain)."""
        return self._embedding_id

    def set_embedding_id(self, embedding_id: str) -> None:
        """Associate vector store embedding reference string."""
        if not embedding_id or not isinstance(embedding_id, str):
            raise ValueError("embedding_id cannot be empty")
        self._embedding_id = embedding_id
