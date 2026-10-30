"""
Thin FastAPI Knowledge Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from knowledge.application.commands.create_knowledge_base import (
    CreateKnowledgeBaseCommand,
    CreateKnowledgeBaseHandler,
)
from knowledge.application.commands.delete_document import (
    DeleteDocumentCommand,
    DeleteDocumentHandler,
)
from knowledge.application.commands.reindex_knowledge_base import (
    ReindexKnowledgeBaseCommand,
    ReindexKnowledgeBaseHandler,
)
from knowledge.application.commands.upload_document import (
    UploadDocumentCommand,
    UploadDocumentHandler,
)
from knowledge.application.dto.knowledge_dto import DocumentDTO, KnowledgeBaseDTO
from knowledge.application.queries.get_knowledge_base import (
    GetKnowledgeBaseHandler,
    GetKnowledgeBaseQuery,
)
from knowledge.application.queries.list_documents import (
    ListDocumentsHandler,
    ListDocumentsQuery,
)
from knowledge.application.queries.search_metadata import (
    SearchMetadataHandler,
    SearchMetadataQuery,
)
from knowledge.presentation.schemas.requests import (
    CreateKnowledgeBaseRequest,
    SearchMetadataRequest,
    UploadDocumentRequest,
)
from knowledge.presentation.schemas.responses import (
    ChunkResponse,
    DocumentMetadataResponse,
    DocumentResponse,
    KnowledgeBaseResponse,
    RetrievalPolicyResponse,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Management"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "INVALID_STATE": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


def _to_doc_response(dto: DocumentDTO) -> DocumentResponse:
    return DocumentResponse(
        id=dto.id,
        file_name=dto.file_name,
        status=dto.status,
        metadata=DocumentMetadataResponse(
            file_type=dto.metadata.file_type,
            size_bytes=dto.metadata.size_bytes,
            source_url=dto.metadata.source_url,
            mime_type=dto.metadata.mime_type,
            tags=dto.metadata.tags,
        ),
        chunk_count=dto.chunk_count,
        created_at=dto.created_at,
        chunks=[
            ChunkResponse(
                id=c.id,
                text_content=c.text_content,
                sequence_index=c.sequence_index,
                token_count=c.token_count,
                embedding_id=c.embedding_id,
                created_at=c.created_at,
            )
            for c in dto.chunks
        ],
    )


def _to_kb_response(dto: KnowledgeBaseDTO) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        name=dto.name,
        description=dto.description,
        status=dto.status,
        retrieval_policy=RetrievalPolicyResponse(
            top_k=dto.retrieval_policy.top_k,
            similarity_threshold=dto.retrieval_policy.similarity_threshold,
            strategy=dto.retrieval_policy.strategy,
            reranking_enabled=dto.retrieval_policy.reranking_enabled,
        ),
        document_count=dto.document_count,
        total_chunks=dto.total_chunks,
        version=dto.version,
        created_at=dto.created_at,
        documents=[_to_doc_response(d) for d in dto.documents],
    )


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new KnowledgeBase",
)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    handler: CreateKnowledgeBaseHandler = Depends(),
) -> KnowledgeBaseResponse:
    """Endpoint dispatching CreateKnowledgeBaseCommand."""
    command = CreateKnowledgeBaseCommand(
        workspace_id=request.workspace_id,
        name=request.name,
        description=request.description,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        strategy=request.strategy,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_kb_response(result.value)


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get KnowledgeBase details by ID",
)
async def get_knowledge_base(
    kb_id: str,
    handler: GetKnowledgeBaseHandler = Depends(),
) -> KnowledgeBaseResponse:
    """Endpoint dispatching GetKnowledgeBaseQuery."""
    query = GetKnowledgeBaseQuery(kb_id=kb_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_kb_response(result.value)


@router.post(
    "/{kb_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Document in KnowledgeBase",
)
async def upload_document(
    kb_id: str,
    request: UploadDocumentRequest,
    handler: UploadDocumentHandler = Depends(),
) -> DocumentResponse:
    """Endpoint dispatching UploadDocumentCommand."""
    command = UploadDocumentCommand(
        kb_id=kb_id,
        file_name=request.file_name,
        file_type=request.file_type,
        size_bytes=request.size_bytes,
        source_url=request.source_url,
        tags=request.tags,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_doc_response(result.value)


@router.delete(
    "/{kb_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document from KnowledgeBase",
)
async def delete_document(
    kb_id: str,
    document_id: str,
    handler: DeleteDocumentHandler = Depends(),
) -> None:
    """Endpoint dispatching DeleteDocumentCommand."""
    command = DeleteDocumentCommand(kb_id=kb_id, document_id=document_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)


@router.post(
    "/{kb_id}/reindex",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate KnowledgeBase reindexing",
)
async def reindex_knowledge_base(
    kb_id: str,
    handler: ReindexKnowledgeBaseHandler = Depends(),
) -> KnowledgeBaseResponse:
    """Endpoint dispatching ReindexKnowledgeBaseCommand."""
    command = ReindexKnowledgeBaseCommand(kb_id=kb_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_kb_response(result.value)


@router.get(
    "/{kb_id}/documents",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Documents in KnowledgeBase",
)
async def list_documents(
    kb_id: str,
    handler: ListDocumentsHandler = Depends(),
) -> list[DocumentResponse]:
    """Endpoint dispatching ListDocumentsQuery."""
    query = ListDocumentsQuery(kb_id=kb_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return [_to_doc_response(d) for d in result.value]


@router.post(
    "/{kb_id}/search",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Search Document metadata tags (non-vector filter)",
)
async def search_metadata(
    kb_id: str,
    request: SearchMetadataRequest,
    handler: SearchMetadataHandler = Depends(),
) -> list[DocumentResponse]:
    """Endpoint dispatching SearchMetadataQuery."""
    query = SearchMetadataQuery(
        kb_id=kb_id,
        file_type=request.file_type,
        tag_key=request.tag_key,
        tag_value=request.tag_value,
    )
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return [_to_doc_response(d) for d in result.value]
