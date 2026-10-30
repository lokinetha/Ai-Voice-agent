"""
Knowledge Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.application.commands.create_knowledge_base import (
    CreateKnowledgeBaseHandler,
)
from knowledge.application.commands.delete_document import (
    DeleteDocumentHandler,
)
from knowledge.application.commands.reindex_knowledge_base import (
    ReindexKnowledgeBaseHandler,
)
from knowledge.application.commands.upload_document import (
    UploadDocumentHandler,
)
from knowledge.application.queries.get_knowledge_base import (
    GetKnowledgeBaseHandler,
)
from knowledge.application.queries.list_documents import ListDocumentsHandler
from knowledge.application.queries.search_metadata import SearchMetadataHandler
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.services.knowledge_base_indexing_service import (
    KnowledgeBaseIndexingService,
)
from knowledge.infrastructure.persistence.sqlalchemy_knowledge_base_repository import (
    SqlAlchemyKnowledgeBaseRepository,
)


class KnowledgeContainer:
    """Dependency Container for Knowledge Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._kb_repository: KnowledgeBaseRepository = (
            SqlAlchemyKnowledgeBaseRepository(session)
        )
        self._indexing_service = KnowledgeBaseIndexingService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def kb_repository(self) -> KnowledgeBaseRepository:
        return self._kb_repository

    @property
    def indexing_service(self) -> KnowledgeBaseIndexingService:
        return self._indexing_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_create_knowledge_base_handler(self) -> CreateKnowledgeBaseHandler:
        return CreateKnowledgeBaseHandler(
            kb_repository=self._kb_repository,
            unit_of_work=self._uow,
        )

    def get_upload_document_handler(self) -> UploadDocumentHandler:
        return UploadDocumentHandler(
            kb_repository=self._kb_repository,
            unit_of_work=self._uow,
        )

    def get_delete_document_handler(self) -> DeleteDocumentHandler:
        return DeleteDocumentHandler(
            kb_repository=self._kb_repository,
            unit_of_work=self._uow,
        )

    def get_reindex_knowledge_base_handler(self) -> ReindexKnowledgeBaseHandler:
        return ReindexKnowledgeBaseHandler(
            kb_repository=self._kb_repository,
            indexing_service=self._indexing_service,
            unit_of_work=self._uow,
        )

    def get_knowledge_base_handler(self) -> GetKnowledgeBaseHandler:
        return GetKnowledgeBaseHandler(
            kb_repository=self._kb_repository,
        )

    def get_list_documents_handler(self) -> ListDocumentsHandler:
        return ListDocumentsHandler(
            kb_repository=self._kb_repository,
        )

    def get_search_metadata_handler(self) -> SearchMetadataHandler:
        return SearchMetadataHandler(
            kb_repository=self._kb_repository,
        )
