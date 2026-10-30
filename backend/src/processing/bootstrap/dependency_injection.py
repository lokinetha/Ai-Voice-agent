"""
Processing Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from conversation.infrastructure.persistence.sqlalchemy_conversation_repository import (
    SqlAlchemyConversationRepository,
)
from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from processing.application.commands.aggregate_behavior_patterns import (
    AggregateBehaviorPatternsHandler,
)
from processing.application.commands.analyze_conversation import (
    AnalyzeConversationHandler,
)
from processing.application.commands.chunk_document import (
    ChunkDocumentHandler,
)
from processing.application.commands.detect_behavior_patterns import (
    DetectBehaviorPatternsHandler,
)
from processing.application.commands.generate_embeddings import (
    GenerateEmbeddingsHandler,
)
from processing.application.commands.process_document import (
    ProcessDocumentHandler,
)
from processing.application.queries.get_behavior_patterns import (
    GetBehaviorPatternsHandler,
)
from processing.application.queries.get_conversation_analysis import (
    GetConversationAnalysisHandler,
)
from processing.application.queries.get_processing_job import (
    GetProcessingJobHandler,
)
from processing.application.queries.list_processing_jobs import (
    ListProcessingJobsHandler,
)
from processing.domain.ports.behavior_analyzer_port import BehaviorAnalyzerPort
from processing.domain.ports.chunking_port import ChunkingPort
from processing.domain.ports.conversation_reader_port import (
    ConversationReaderPort,
)
from processing.domain.ports.document_parser_port import DocumentParserPort
from processing.domain.ports.embedding_port import EmbeddingPort
from processing.domain.ports.object_storage_port import ObjectStoragePort
from processing.domain.ports.transcript_provider_port import (
    TranscriptProviderPort,
)
from processing.domain.ports.vector_store_port import VectorStorePort
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)
from processing.domain.services.processing_validation_service import (
    ProcessingValidationService,
)
from processing.infrastructure.adapters.chunking_adapter import ChunkingAdapter
from processing.infrastructure.adapters.conversation_reader_adapter import (
    ConversationReaderAdapter,
)
from processing.infrastructure.adapters.deterministic_behavior_analyzer_adapter import (
    DeterministicBehaviorAnalyzerAdapter,
)
from processing.infrastructure.adapters.embedding_adapter import EmbeddingAdapter
from processing.infrastructure.adapters.object_storage_adapter import (
    ObjectStorageAdapter,
)
from processing.infrastructure.adapters.pdf_parser_adapter import PDFParserAdapter
from processing.infrastructure.adapters.transcript_adapter import (
    TranscriptAdapter,
)
from processing.infrastructure.adapters.vector_store_adapter import (
    VectorStoreAdapter,
)
from processing.infrastructure.persistence.sqlalchemy_conversation_analysis_repository import (
    SqlAlchemyConversationAnalysisRepository,
)
from processing.infrastructure.persistence.sqlalchemy_processing_job_repository import (
    SqlAlchemyProcessingJobRepository,
)


class ProcessingContainer:
    """Dependency Container for Processing Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._job_repository: ProcessingJobRepository = (
            SqlAlchemyProcessingJobRepository(session)
        )
        self._analysis_repository: ConversationAnalysisRepository = (
            SqlAlchemyConversationAnalysisRepository(session)
        )

        conv_repo = SqlAlchemyConversationRepository(session)
        self._conversation_reader_port: ConversationReaderPort = (
            ConversationReaderAdapter(conv_repo)
        )
        self._transcript_provider_port: TranscriptProviderPort = (
            TranscriptAdapter(conv_repo)
        )
        self._behavior_analyzer_port: BehaviorAnalyzerPort = (
            DeterministicBehaviorAnalyzerAdapter()
        )

        self._object_storage_port: ObjectStoragePort = ObjectStorageAdapter()
        self._parser_port: DocumentParserPort = PDFParserAdapter()
        self._chunking_port: ChunkingPort = ChunkingAdapter()
        self._embedding_port: EmbeddingPort = EmbeddingAdapter()
        self._vector_store_port: VectorStorePort = VectorStoreAdapter()
        self._validation_service = ProcessingValidationService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def job_repository(self) -> ProcessingJobRepository:
        return self._job_repository

    @property
    def analysis_repository(self) -> ConversationAnalysisRepository:
        return self._analysis_repository

    @property
    def conversation_reader_port(self) -> ConversationReaderPort:
        return self._conversation_reader_port

    @property
    def transcript_provider_port(self) -> TranscriptProviderPort:
        return self._transcript_provider_port

    @property
    def behavior_analyzer_port(self) -> BehaviorAnalyzerPort:
        return self._behavior_analyzer_port

    @property
    def object_storage_port(self) -> ObjectStoragePort:
        return self._object_storage_port

    @property
    def parser_port(self) -> DocumentParserPort:
        return self._parser_port

    @property
    def chunking_port(self) -> ChunkingPort:
        return self._chunking_port

    @property
    def embedding_port(self) -> EmbeddingPort:
        return self._embedding_port

    @property
    def vector_store_port(self) -> VectorStorePort:
        return self._vector_store_port

    @property
    def validation_service(self) -> ProcessingValidationService:
        return self._validation_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_process_document_handler(self) -> ProcessDocumentHandler:
        return ProcessDocumentHandler(
            job_repository=self._job_repository,
            object_storage_port=self._object_storage_port,
            parser_port=self._parser_port,
            chunking_port=self._chunking_port,
            embedding_port=self._embedding_port,
            vector_store_port=self._vector_store_port,
            unit_of_work=self._uow,
        )

    def get_chunk_document_handler(self) -> ChunkDocumentHandler:
        return ChunkDocumentHandler(chunking_port=self._chunking_port)

    def get_generate_embeddings_handler(self) -> GenerateEmbeddingsHandler:
        return GenerateEmbeddingsHandler(embedding_port=self._embedding_port)

    def get_processing_job_handler(self) -> GetProcessingJobHandler:
        return GetProcessingJobHandler(job_repository=self._job_repository)

    def get_list_processing_jobs_handler(self) -> ListProcessingJobsHandler:
        return ListProcessingJobsHandler(job_repository=self._job_repository)

    def get_analyze_conversation_handler(self) -> AnalyzeConversationHandler:
        return AnalyzeConversationHandler(
            analysis_repository=self._analysis_repository,
            conversation_reader_port=self._conversation_reader_port,
            transcript_provider_port=self._transcript_provider_port,
            behavior_analyzer_port=self._behavior_analyzer_port,
            unit_of_work=self._uow,
        )

    def get_detect_behavior_patterns_handler(self) -> DetectBehaviorPatternsHandler:
        return DetectBehaviorPatternsHandler(
            behavior_analyzer_port=self._behavior_analyzer_port
        )

    def get_aggregate_behavior_patterns_handler(self) -> AggregateBehaviorPatternsHandler:
        return AggregateBehaviorPatternsHandler(
            analysis_repository=self._analysis_repository
        )

    def get_conversation_analysis_handler(self) -> GetConversationAnalysisHandler:
        return GetConversationAnalysisHandler(
            analysis_repository=self._analysis_repository
        )

    def get_behavior_patterns_handler(self) -> GetBehaviorPatternsHandler:
        return GetBehaviorPatternsHandler(
            analysis_repository=self._analysis_repository
        )
