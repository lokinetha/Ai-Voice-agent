"""
Prompt Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from playbook.infrastructure.persistence.sqlalchemy_playbook_repository import (
    SqlAlchemyPlaybookRepository,
)
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from prompt.application.commands.archive_prompt import (
    ArchivePromptHandler,
)
from prompt.application.commands.compile_prompt import (
    CompilePromptHandler,
)
from prompt.application.commands.create_prompt import (
    CreatePromptHandler,
)
from prompt.application.commands.create_prompt_version import (
    CreatePromptVersionHandler,
)
from prompt.application.commands.publish_prompt import (
    PublishPromptHandler,
)
from prompt.application.commands.update_prompt import (
    UpdatePromptHandler,
)
from prompt.application.queries.get_prompt import (
    GetPromptHandler,
)
from prompt.application.queries.get_prompt_version import (
    GetPromptVersionHandler,
)
from prompt.application.queries.list_prompts import (
    ListPromptsHandler,
)
from prompt.domain.ports.playbook_port import PlaybookQueryPort
from prompt.domain.repositories.prompt_repository import PromptRepository
from prompt.domain.services.prompt_compilation_service import (
    PromptCompilationService,
)
from prompt.domain.services.prompt_validation_service import (
    PromptValidationService,
)
from prompt.infrastructure.adapters.playbook_adapter import (
    PlaybookRepositoryAdapter,
)
from prompt.infrastructure.persistence.sqlalchemy_prompt_repository import (
    SqlAlchemyPromptRepository,
)


class PromptContainer:
    """Dependency Container for Prompt Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._prompt_repository: PromptRepository = SqlAlchemyPromptRepository(session)
        self._playbook_repository = SqlAlchemyPlaybookRepository(session)
        self._playbook_port: PlaybookQueryPort = PlaybookRepositoryAdapter(
            self._playbook_repository
        )
        self._compilation_service = PromptCompilationService()
        self._validation_service = PromptValidationService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def prompt_repository(self) -> PromptRepository:
        return self._prompt_repository

    @property
    def playbook_port(self) -> PlaybookQueryPort:
        return self._playbook_port

    @property
    def compilation_service(self) -> PromptCompilationService:
        return self._compilation_service

    @property
    def validation_service(self) -> PromptValidationService:
        return self._validation_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_create_prompt_handler(self) -> CreatePromptHandler:
        return CreatePromptHandler(
            prompt_repository=self._prompt_repository,
            unit_of_work=self._uow,
        )

    def get_compile_prompt_handler(self) -> CompilePromptHandler:
        return CompilePromptHandler(
            prompt_repository=self._prompt_repository,
            playbook_port=self._playbook_port,
            compilation_service=self._compilation_service,
            unit_of_work=self._uow,
        )

    def get_update_prompt_handler(self) -> UpdatePromptHandler:
        return UpdatePromptHandler(
            prompt_repository=self._prompt_repository,
            unit_of_work=self._uow,
        )

    def get_publish_prompt_handler(self) -> PublishPromptHandler:
        return PublishPromptHandler(
            prompt_repository=self._prompt_repository,
            validation_service=self._validation_service,
            unit_of_work=self._uow,
        )

    def get_archive_prompt_handler(self) -> ArchivePromptHandler:
        return ArchivePromptHandler(
            prompt_repository=self._prompt_repository,
            unit_of_work=self._uow,
        )

    def get_create_prompt_version_handler(self) -> CreatePromptVersionHandler:
        return CreatePromptVersionHandler(
            prompt_repository=self._prompt_repository,
            unit_of_work=self._uow,
        )

    def get_prompt_handler(self) -> GetPromptHandler:
        return GetPromptHandler(prompt_repository=self._prompt_repository)

    def get_list_prompts_handler(self) -> ListPromptsHandler:
        return ListPromptsHandler(prompt_repository=self._prompt_repository)

    def get_prompt_version_handler(self) -> GetPromptVersionHandler:
        return GetPromptVersionHandler(prompt_repository=self._prompt_repository)
