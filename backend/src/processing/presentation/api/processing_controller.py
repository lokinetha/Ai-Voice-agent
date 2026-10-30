"""
Thin FastAPI Processing Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from processing.application.commands.aggregate_behavior_patterns import (
    AggregateBehaviorPatternsCommand,
    AggregateBehaviorPatternsHandler,
)
from processing.application.commands.analyze_conversation import (
    AnalyzeConversationCommand,
    AnalyzeConversationHandler,
)
from processing.application.commands.chunk_document import (
    ChunkDocumentCommand,
    ChunkDocumentHandler,
)
from processing.application.commands.detect_behavior_patterns import (
    DetectBehaviorPatternsCommand,
    DetectBehaviorPatternsHandler,
)
from processing.application.commands.generate_embeddings import (
    GenerateEmbeddingsCommand,
    GenerateEmbeddingsHandler,
)
from processing.application.commands.process_document import (
    ProcessDocumentCommand,
    ProcessDocumentHandler,
)
from processing.application.dto.conversation_analysis_dto import (
    ConversationAnalysisDTO,
)
from processing.application.dto.processing_dto import ProcessingJobDTO
from processing.application.queries.get_behavior_patterns import (
    GetBehaviorPatternsHandler,
    GetBehaviorPatternsQuery,
)
from processing.application.queries.get_conversation_analysis import (
    GetConversationAnalysisHandler,
    GetConversationAnalysisQuery,
)
from processing.application.queries.get_processing_job import (
    GetProcessingJobHandler,
    GetProcessingJobQuery,
)
from processing.application.queries.list_processing_jobs import (
    ListProcessingJobsHandler,
    ListProcessingJobsQuery,
)
from processing.presentation.schemas.requests import (
    AnalyzeConversationRequest,
    ChunkDocumentRequest,
    DetectBehaviorPatternsRequest,
    GenerateEmbeddingsRequest,
    ProcessDocumentRequest,
)
from processing.presentation.schemas.responses import (
    AnalysisResultResponse,
    BehavioralSignalResponse,
    ChunkDocumentResponse,
    ChunkingStrategyResponse,
    ConversationAnalysisResponse,
    ConversationPatternResponse,
    EmbeddingStrategyResponse,
    GenerateEmbeddingsResponse,
    ProcessingJobResponse,
    ProcessingResultResponse,
    ProcessingTaskResponse,
)

router = APIRouter(prefix="/processing", tags=["Knowledge & Conversation Processing"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "INVALID_STATE": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVARIANT_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


def _to_job_response(dto: ProcessingJobDTO) -> ProcessingJobResponse:
    chunking = ChunkingStrategyResponse(
        strategy_type=dto.chunking_strategy.strategy_type,
        chunk_size=dto.chunking_strategy.chunk_size,
        chunk_overlap=dto.chunking_strategy.chunk_overlap,
    )

    embedding = EmbeddingStrategyResponse(
        model_name=dto.embedding_strategy.model_name,
        dimension=dto.embedding_strategy.dimension,
    )

    tasks = []
    for t in dto.tasks:
        res = None
        if t.result is not None:
            res = ProcessingResultResponse(
                output_count=t.result.output_count,
                execution_time_seconds=t.result.execution_time_seconds,
                metrics=t.result.metrics,
                metadata=t.result.metadata,
            )
        tasks.append(
            ProcessingTaskResponse(
                id=t.id,
                task_type=t.task_type,
                order=t.order,
                status=t.status,
                result=res,
                error_message=t.error_message,
            )
        )

    return ProcessingJobResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        document_id=dto.document_id,
        status=dto.status,
        chunking_strategy=chunking,
        embedding_strategy=embedding,
        tasks=tasks,
        chunk_references=list(dto.chunk_references),
        vector_references=list(dto.vector_references),
        error_message=dto.error_message,
        version=dto.version,
        created_at=dto.created_at,
    )


def _to_analysis_response(dto: ConversationAnalysisDTO) -> ConversationAnalysisResponse:
    res = None
    if dto.result is not None:
        res = AnalysisResultResponse(
            signals_count=dto.result.signals_count,
            patterns_count=dto.result.patterns_count,
            execution_time_seconds=dto.result.execution_time_seconds,
            summary=dto.result.summary,
            metadata=dto.result.metadata,
        )

    signals = [
        BehavioralSignalResponse(
            id=s.id,
            category=s.category,
            signal_type=s.signal_type,
            description=s.description,
            confidence=s.confidence,
            source_message_id=s.source_message_id,
            evidence_text=s.evidence_text,
        )
        for s in dto.signals
    ]

    patterns = [
        ConversationPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            category=p.category,
            description=p.description,
            frequency=p.frequency,
            confidence=p.confidence,
            sample_signal_ids=list(p.sample_signal_ids),
            conversation_references=list(p.conversation_references),
        )
        for p in dto.patterns
    ]

    return ConversationAnalysisResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        conversation_id=dto.conversation_id,
        status=dto.status,
        signals=signals,
        patterns=patterns,
        result=res,
        error_message=dto.error_message,
        version=dto.version,
        created_at=dto.created_at,
    )


@router.post(
    "/process",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process Document end-to-end",
)
async def process_document(
    request: ProcessDocumentRequest,
    handler: ProcessDocumentHandler = Depends(),
) -> ProcessingJobResponse:
    """Endpoint dispatching ProcessDocumentCommand."""
    command = ProcessDocumentCommand(
        workspace_id=request.workspace_id,
        document_id=request.document_id,
        storage_bucket=request.storage_bucket,
        storage_key=request.storage_key,
        file_type=request.file_type,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        embedding_model=request.embedding_model,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_job_response(result.value)


@router.post(
    "/chunk",
    response_model=ChunkDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Chunk document text",
)
async def chunk_document(
    request: ChunkDocumentRequest,
    handler: ChunkDocumentHandler = Depends(),
) -> ChunkDocumentResponse:
    """Endpoint dispatching ChunkDocumentCommand."""
    command = ChunkDocumentCommand(
        text=request.text,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        strategy_type=request.strategy_type,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return ChunkDocumentResponse(chunks=list(result.value))


@router.post(
    "/embed",
    response_model=GenerateEmbeddingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate vector embeddings",
)
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    handler: GenerateEmbeddingsHandler = Depends(),
) -> GenerateEmbeddingsResponse:
    """Endpoint dispatching GenerateEmbeddingsCommand."""
    command = GenerateEmbeddingsCommand(
        texts=tuple(request.texts),
        model_name=request.model_name,
        dimension=request.dimension,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return GenerateEmbeddingsResponse(vectors=[list(v) for v in result.value])


@router.get(
    "/jobs/{job_id}",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ProcessingJob details",
)
async def get_processing_job(
    job_id: str,
    handler: GetProcessingJobHandler = Depends(),
) -> ProcessingJobResponse:
    """Endpoint dispatching GetProcessingJobQuery."""
    query = GetProcessingJobQuery(job_id=job_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_job_response(result.value)


@router.get(
    "/jobs",
    response_model=list[ProcessingJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List ProcessingJobs by Workspace",
)
async def list_processing_jobs(
    workspace_id: str,
    handler: ListProcessingJobsHandler = Depends(),
) -> list[ProcessingJobResponse]:
    """Endpoint dispatching ListProcessingJobsQuery."""
    query = ListProcessingJobsQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_job_response(j) for j in result.value]


# ── Conversation Analysis Endpoints ─────────────────────────────────────


@router.post(
    "/analyze-conversation",
    response_model=ConversationAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze completed conversation",
)
async def analyze_conversation(
    request: AnalyzeConversationRequest,
    handler: AnalyzeConversationHandler = Depends(),
) -> ConversationAnalysisResponse:
    """Endpoint dispatching AnalyzeConversationCommand."""
    command = AnalyzeConversationCommand(
        workspace_id=request.workspace_id,
        conversation_id=request.conversation_id,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_analysis_response(result.value)


@router.post(
    "/detect-patterns",
    response_model=list[ConversationPatternResponse],
    status_code=status.HTTP_200_OK,
    summary="Detect behavior patterns in messages",
)
async def detect_behavior_patterns(
    request: DetectBehaviorPatternsRequest,
    handler: DetectBehaviorPatternsHandler = Depends(),
) -> list[ConversationPatternResponse]:
    """Endpoint dispatching DetectBehaviorPatternsCommand."""
    command = DetectBehaviorPatternsCommand(
        messages=tuple(request.messages),
        conversation_id=request.conversation_id,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [
        ConversationPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            category=p.category,
            description=p.description,
            frequency=p.frequency,
            confidence=p.confidence,
            sample_signal_ids=list(p.sample_signal_ids),
            conversation_references=list(p.conversation_references),
        )
        for p in result.value
    ]


@router.post(
    "/aggregate-patterns",
    response_model=list[ConversationPatternResponse],
    status_code=status.HTTP_200_OK,
    summary="Aggregate behavior patterns across workspace",
)
async def aggregate_behavior_patterns(
    workspace_id: str,
    handler: AggregateBehaviorPatternsHandler = Depends(),
) -> list[ConversationPatternResponse]:
    """Endpoint dispatching AggregateBehaviorPatternsCommand."""
    command = AggregateBehaviorPatternsCommand(workspace_id=workspace_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [
        ConversationPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            category=p.category,
            description=p.description,
            frequency=p.frequency,
            confidence=p.confidence,
            sample_signal_ids=list(p.sample_signal_ids),
            conversation_references=list(p.conversation_references),
        )
        for p in result.value
    ]


@router.get(
    "/analyses/{analysis_id}",
    response_model=ConversationAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ConversationAnalysis details",
)
async def get_conversation_analysis(
    analysis_id: str,
    handler: GetConversationAnalysisHandler = Depends(),
) -> ConversationAnalysisResponse:
    """Endpoint dispatching GetConversationAnalysisQuery."""
    query = GetConversationAnalysisQuery(analysis_id=analysis_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_analysis_response(result.value)


@router.get(
    "/patterns",
    response_model=list[ConversationPatternResponse],
    status_code=status.HTTP_200_OK,
    summary="Get behavior patterns by workspace",
)
async def get_behavior_patterns(
    workspace_id: str,
    handler: GetBehaviorPatternsHandler = Depends(),
) -> list[ConversationPatternResponse]:
    """Endpoint dispatching GetBehaviorPatternsQuery."""
    query = GetBehaviorPatternsQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [
        ConversationPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            category=p.category,
            description=p.description,
            frequency=p.frequency,
            confidence=p.confidence,
            sample_signal_ids=list(p.sample_signal_ids),
            conversation_references=list(p.conversation_references),
        )
        for p in result.value
    ]
