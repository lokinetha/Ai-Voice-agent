"""
Document Entity for Knowledge Bounded Context.

Represents a knowledge document file owned by KnowledgeBase aggregate.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.entity import Entity
from shared.kernel.result import Result
from shared.kernel.value_objects import DocumentId, EntityId, Timestamp

from knowledge.domain.entities.chunk import Chunk
from knowledge.domain.value_objects.document_metadata import DocumentMetadata
from knowledge.domain.value_objects.document_status import DocumentStatus


class Document(Entity[DocumentId]):
    """Document Entity child of KnowledgeBase aggregate root."""

    def __init__(
        self,
        id: DocumentId,
        file_name: str,
        metadata: DocumentMetadata,
        status: DocumentStatus = DocumentStatus.pending(),
        chunks: Sequence[Chunk] = (),
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not file_name or not isinstance(file_name, str) or not file_name.strip():
            raise ValueError("Document file_name cannot be empty")

        self._file_name = file_name.strip()
        self._metadata = metadata
        self._status = status
        self._chunks: dict[EntityId, Chunk] = {c.id: c for c in chunks}

    @property
    def file_name(self) -> str:
        return self._file_name

    @property
    def metadata(self) -> DocumentMetadata:
        return self._metadata

    @property
    def status(self) -> DocumentStatus:
        return self._status

    @property
    def chunks(self) -> tuple[Chunk, ...]:
        return tuple(self._chunks.values())

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def add_chunk(self, chunk: Chunk) -> Result[None]:
        """Add chunk child entity to Document."""
        self._chunks[chunk.id] = chunk
        return Result.ok(None)

    def mark_indexed(self) -> Result[None]:
        """Set document status to INDEXED."""
        self._status = DocumentStatus.indexed()
        return Result.ok(None)

    def mark_failed(self) -> Result[None]:
        """Set document status to FAILED."""
        self._status = DocumentStatus.failed()
        return Result.ok(None)
