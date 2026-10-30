"""
Playbook Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from playbook.application.commands.archive_playbook import (
    ArchivePlaybookHandler,
)
from playbook.application.commands.create_playbook import (
    CreatePlaybookHandler,
)
from playbook.application.commands.create_playbook_version import (
    CreatePlaybookVersionHandler,
)
from playbook.application.commands.publish_playbook import (
    PublishPlaybookHandler,
)
from playbook.application.commands.update_playbook import (
    UpdatePlaybookHandler,
)
from playbook.application.queries.get_playbook import (
    GetPlaybookHandler,
)
from playbook.application.queries.get_playbook_version import (
    GetPlaybookVersionHandler,
)
from playbook.application.queries.list_playbooks import (
    ListPlaybooksHandler,
)
from playbook.domain.repositories.playbook_repository import PlaybookRepository
from playbook.domain.services.playbook_validation_service import (
    PlaybookValidationService,
)
from playbook.infrastructure.persistence.sqlalchemy_playbook_repository import (
    SqlAlchemyPlaybookRepository,
)


class PlaybookContainer:
    """Dependency Container for Playbook Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._playbook_repository: PlaybookRepository = (
            SqlAlchemyPlaybookRepository(session)
        )
        self._validation_service = PlaybookValidationService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def playbook_repository(self) -> PlaybookRepository:
        return self._playbook_repository

    @property
    def validation_service(self) -> PlaybookValidationService:
        return self._validation_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_create_playbook_handler(self) -> CreatePlaybookHandler:
        return CreatePlaybookHandler(
            playbook_repository=self._playbook_repository,
            unit_of_work=self._uow,
        )

    def get_update_playbook_handler(self) -> UpdatePlaybookHandler:
        return UpdatePlaybookHandler(
            playbook_repository=self._playbook_repository,
            unit_of_work=self._uow,
        )

    def get_publish_playbook_handler(self) -> PublishPlaybookHandler:
        return PublishPlaybookHandler(
            playbook_repository=self._playbook_repository,
            validation_service=self._validation_service,
            unit_of_work=self._uow,
        )

    def get_archive_playbook_handler(self) -> ArchivePlaybookHandler:
        return ArchivePlaybookHandler(
            playbook_repository=self._playbook_repository,
            unit_of_work=self._uow,
        )

    def get_create_playbook_version_handler(self) -> CreatePlaybookVersionHandler:
        return CreatePlaybookVersionHandler(
            playbook_repository=self._playbook_repository,
            unit_of_work=self._uow,
        )

    def get_playbook_handler(self) -> GetPlaybookHandler:
        return GetPlaybookHandler(playbook_repository=self._playbook_repository)

    def get_list_playbooks_handler(self) -> ListPlaybooksHandler:
        return ListPlaybooksHandler(playbook_repository=self._playbook_repository)

    def get_playbook_version_handler(self) -> GetPlaybookVersionHandler:
        return GetPlaybookVersionHandler(
            playbook_repository=self._playbook_repository
        )
