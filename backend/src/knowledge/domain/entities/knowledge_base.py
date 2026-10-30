"""
KnowledgeBase Aggregate Root for Knowledge Bounded Context.

Central Aggregate Root managing knowledge document collections, indexing status,
and retrieval policy configurations.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    DocumentId,
    KnowledgeBaseId,
    Timestamp,
    WorkspaceId,
)

from knowledge.domain.entities.document import Document
from knowledge.domain.events.document_deleted import DocumentDeleted
from knowledge.domain.events.document_uploaded import DocumentUploaded
from knowledge.domain.events.knowledge_base_reindexed import (
    KnowledgeBaseReindexed,
)
from knowledge.domain.value_objects.kb_status import KnowledgeBaseStatus
from knowledge.domain.value_objects.retrieval_policy import RetrievalPolicy


class KnowledgeBase(AggregateRoot[KnowledgeBaseId]):
    """KnowledgeBase Aggregate Root."""

    def __init__(
        self,
        id: KnowledgeBaseId,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        status: KnowledgeBaseStatus = KnowledgeBaseStatus.active(),
        retrieval_policy: RetrievalPolicy | None = None,
        documents: Sequence[Document] = (),
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("KnowledgeBase name cannot be empty")

        self._workspace_id = workspace_id
        self._name = name.strip()
        self._description = description.strip()
        self._status = status
        self._retrieval_policy = retrieval_policy or RetrievalPolicy.default()
        self._documents: dict[DocumentId, Document] = {d.id: d for d in documents}

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> KnowledgeBaseStatus:
        return self._status

    @property
    def retrieval_policy(self) -> RetrievalPolicy:
        return self._retrieval_policy

    @property
    def documents(self) -> tuple[Document, ...]:
        return tuple(self._documents.values())

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @property
    def total_chunks(self) -> int:
        return sum(d.chunk_count for d in self._documents.values())

    def get_document(self, document_id: DocumentId) -> Document | None:
        return self._documents.get(document_id)

    def add_document(self, document: Document) -> Result[None]:
        """Add Document entity to KnowledgeBase aggregate."""
        if document.id in self._documents:
            return Result.fail(
                Error("CONFLICT", f"Document '{document.id.value}' already exists in KnowledgeBase")
            )

        self._documents[document.id] = document
        self._raise_event(
            DocumentUploaded(
                kb_id=str(self.id.value),
                document_id=str(document.id.value),
                file_name=document.file_name,
                size_bytes=document.metadata.size_bytes,
            )
        )
        return Result.ok(None)

    def remove_document(self, document_id: DocumentId) -> Result[None]:
        """Remove Document entity from KnowledgeBase aggregate."""
        if document_id not in self._documents:
            return Result.fail(
                Error("NOT_FOUND", f"Document '{document_id.value}' not found in KnowledgeBase")
            )

        del self._documents[document_id]
        self._raise_event(
            DocumentDeleted(
                kb_id=str(self.id.value),
                document_id=str(document_id.value),
            )
        )
        return Result.ok(None)

    def update_retrieval_policy(self, policy: RetrievalPolicy) -> Result[None]:
        """Update RetrievalPolicy value object."""
        self._retrieval_policy = policy
        return Result.ok(None)

    def reindex(self) -> Result[None]:
        """Initiate reindexing of KnowledgeBase metadata."""
        if self._status == KnowledgeBaseStatus.archived():
            return Result.fail(Error("INVALID_STATE", "Cannot reindex an archived KnowledgeBase"))

        self._status = KnowledgeBaseStatus.indexing()
        self._version += 1

        self._raise_event(
            KnowledgeBaseReindexed(
                kb_id=str(self.id.value),
                document_count=self.document_count,
                total_chunks=self.total_chunks,
            )
        )
        return Result.ok(None)
