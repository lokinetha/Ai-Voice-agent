"""
SQLAlchemy 2.x Repository Implementation for KnowledgeBase Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    DocumentId,
    EntityId,
    KnowledgeBaseId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.domain.entities.chunk import Chunk
from knowledge.domain.entities.document import Document
from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.value_objects.document_metadata import DocumentMetadata
from knowledge.domain.value_objects.document_status import (
    DocumentStatus,
    DocumentStatusType,
)
from knowledge.domain.value_objects.kb_status import (
    KBStatusType,
    KnowledgeBaseStatus,
)
from knowledge.domain.value_objects.retrieval_policy import RetrievalPolicy
from knowledge.infrastructure.persistence.models import (
    ChunkModel,
    DocumentModel,
    KnowledgeBaseModel,
)


class SqlAlchemyKnowledgeBaseRepository(KnowledgeBaseRepository):
    """SQLAlchemy implementation of KnowledgeBaseRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: KnowledgeBaseId) -> KnowledgeBase | None:
        """Retrieve KnowledgeBase aggregate by ID."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> KnowledgeBase | None:
        """Find KnowledgeBase by workspace ID and name string."""
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.workspace_id == str(workspace_id.value),
            KnowledgeBaseModel.name == name.strip(),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[KnowledgeBase]:
        """Find all KnowledgeBases belonging to target WorkspaceId."""
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_aggregate(m) for m in models]

    async def save(self, aggregate: KnowledgeBase) -> None:
        """Persist or update KnowledgeBase aggregate root and all document child entities."""
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.id == str(aggregate.id.value)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = KnowledgeBaseModel(
                id=str(aggregate.id.value),
                workspace_id=str(aggregate.workspace_id.value),
                name=aggregate.name,
                description=aggregate.description,
                status=aggregate.status.value.value,
                top_k=aggregate.retrieval_policy.top_k,
                similarity_threshold=aggregate.retrieval_policy.similarity_threshold,
                strategy=aggregate.retrieval_policy.strategy,
                reranking_enabled=aggregate.retrieval_policy.reranking_enabled,
                version=aggregate.version,
                created_at=aggregate.created_at.value,
                documents=[
                    DocumentModel(
                        id=str(d.id.value),
                        kb_id=str(aggregate.id.value),
                        file_name=d.file_name,
                        status=d.status.value.value,
                        file_type=d.metadata.file_type,
                        size_bytes=d.metadata.size_bytes,
                        source_url=d.metadata.source_url,
                        mime_type=d.metadata.mime_type,
                        tags_json=d.metadata.tags,
                        created_at=d.created_at.value,
                        chunks=[
                            ChunkModel(
                                id=str(c.id.value),
                                document_id=str(d.id.value),
                                text_content=c.text_content,
                                sequence_index=c.sequence_index,
                                token_count=c.token_count,
                                embedding_id=c.embedding_id,
                                created_at=c.created_at.value,
                            )
                            for c in d.chunks
                        ],
                    )
                    for d in aggregate.documents
                ],
            )
            self._session.add(model)
        else:
            existing.name = aggregate.name
            existing.description = aggregate.description
            existing.status = aggregate.status.value.value
            existing.top_k = aggregate.retrieval_policy.top_k
            existing.similarity_threshold = aggregate.retrieval_policy.similarity_threshold
            existing.strategy = aggregate.retrieval_policy.strategy
            existing.reranking_enabled = aggregate.retrieval_policy.reranking_enabled
            existing.version = aggregate.version

    async def delete(self, aggregate: KnowledgeBase) -> None:
        """Delete KnowledgeBase aggregate from persistence."""
        stmt = sql_delete(KnowledgeBaseModel).where(
            KnowledgeBaseModel.id == str(aggregate.id.value)
        )
        await self._session.execute(stmt)

    async def find(self, spec: Specification[KnowledgeBase]) -> list[KnowledgeBase]:
        """Find KnowledgeBase aggregates satisfying specification filter."""
        stmt = select(KnowledgeBaseModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        aggregates = [self._to_aggregate(m) for m in models]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[KnowledgeBase]) -> int:
        """Count KnowledgeBase aggregates satisfying specification filter."""
        aggregates = await self.find(spec)
        return len(aggregates)

    @staticmethod
    def _to_aggregate(model: KnowledgeBaseModel) -> KnowledgeBase:
        """Map ORM KnowledgeBaseModel to domain KnowledgeBase aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        policy = RetrievalPolicy(
            top_k=model.top_k,
            similarity_threshold=model.similarity_threshold,
            strategy=model.strategy,
            reranking_enabled=model.reranking_enabled,
        )

        documents = []
        for d in model.documents:
            doc_created_at = d.created_at
            if doc_created_at and doc_created_at.tzinfo is None:
                doc_created_at = doc_created_at.replace(tzinfo=UTC)

            meta = DocumentMetadata(
                file_type=d.file_type,
                size_bytes=d.size_bytes,
                source_url=d.source_url,
                mime_type=d.mime_type,
                tags=d.tags_json,
            )

            chunks = []
            for c in d.chunks:
                c_created_at = c.created_at
                if c_created_at and c_created_at.tzinfo is None:
                    c_created_at = c_created_at.replace(tzinfo=UTC)

                chunks.append(
                    Chunk(
                        id=EntityId(c.id),
                        text_content=c.text_content,
                        sequence_index=c.sequence_index,
                        token_count=c.token_count,
                        embedding_id=c.embedding_id,
                        created_at=Timestamp(c_created_at),
                    )
                )

            documents.append(
                Document(
                    id=DocumentId(d.id),
                    file_name=d.file_name,
                    metadata=meta,
                    status=DocumentStatus(DocumentStatusType(d.status)),
                    chunks=chunks,
                    created_at=Timestamp(doc_created_at),
                )
            )

        return KnowledgeBase(
            id=KnowledgeBaseId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            name=model.name,
            description=model.description,
            status=KnowledgeBaseStatus(KBStatusType(model.status)),
            retrieval_policy=policy,
            documents=documents,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
