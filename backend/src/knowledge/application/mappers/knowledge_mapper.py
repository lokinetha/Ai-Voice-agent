"""
KnowledgeMapper for mapping between Domain Aggregates/Entities and Application DTOs.
"""

from __future__ import annotations

from knowledge.application.dto.knowledge_dto import (
    ChunkDTO,
    DocumentDTO,
    DocumentMetadataDTO,
    KnowledgeBaseDTO,
    RetrievalPolicyDTO,
)
from knowledge.domain.entities.chunk import Chunk
from knowledge.domain.entities.document import Document
from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.value_objects.document_metadata import DocumentMetadata
from knowledge.domain.value_objects.retrieval_policy import RetrievalPolicy


class KnowledgeMapper:
    """Static mapper for Knowledge domain ↔ DTO conversion."""

    @staticmethod
    def to_kb_dto(kb: KnowledgeBase, include_documents: bool = False) -> KnowledgeBaseDTO:
        """Map KnowledgeBase aggregate root to KnowledgeBaseDTO."""
        docs = (
            tuple(KnowledgeMapper.to_document_dto(d, include_chunks=False) for d in kb.documents)
            if include_documents
            else ()
        )

        return KnowledgeBaseDTO(
            id=str(kb.id.value),
            workspace_id=str(kb.workspace_id.value),
            name=kb.name,
            description=kb.description,
            status=kb.status.value.value,
            retrieval_policy=KnowledgeMapper.to_policy_dto(kb.retrieval_policy),
            document_count=kb.document_count,
            total_chunks=kb.total_chunks,
            version=kb.version,
            created_at=kb.created_at.value,
            documents=docs,
        )

    @staticmethod
    def to_document_dto(doc: Document, include_chunks: bool = False) -> DocumentDTO:
        """Map Document entity to DocumentDTO."""
        chunks = (
            tuple(KnowledgeMapper.to_chunk_dto(c) for c in doc.chunks)
            if include_chunks
            else ()
        )

        return DocumentDTO(
            id=str(doc.id.value),
            file_name=doc.file_name,
            status=doc.status.value.value,
            metadata=KnowledgeMapper.to_metadata_dto(doc.metadata),
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.value,
            chunks=chunks,
        )

    @staticmethod
    def to_chunk_dto(chunk: Chunk) -> ChunkDTO:
        """Map Chunk entity to ChunkDTO."""
        return ChunkDTO(
            id=str(chunk.id.value),
            text_content=chunk.text_content,
            sequence_index=chunk.sequence_index,
            token_count=chunk.token_count,
            embedding_id=chunk.embedding_id,
            created_at=chunk.created_at.value,
        )

    @staticmethod
    def to_policy_dto(policy: RetrievalPolicy) -> RetrievalPolicyDTO:
        return RetrievalPolicyDTO(
            top_k=policy.top_k,
            similarity_threshold=policy.similarity_threshold,
            strategy=policy.strategy,
            reranking_enabled=policy.reranking_enabled,
        )

    @staticmethod
    def to_metadata_dto(metadata: DocumentMetadata) -> DocumentMetadataDTO:
        return DocumentMetadataDTO(
            file_type=metadata.file_type,
            size_bytes=metadata.size_bytes,
            source_url=metadata.source_url,
            mime_type=metadata.mime_type,
            tags=metadata.tags,
        )
