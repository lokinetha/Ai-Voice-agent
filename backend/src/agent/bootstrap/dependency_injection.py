"""
Agent Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from agent.application.commands.archive_agent import ArchiveAgentHandler
from agent.application.commands.clone_agent import CloneAgentHandler
from agent.application.commands.create_agent import CreateAgentHandler
from agent.application.commands.publish_agent import PublishAgentHandler
from agent.application.commands.update_agent import UpdateAgentHandler
from agent.application.queries.get_agent import GetAgentHandler
from agent.application.queries.list_agents import ListAgentsHandler
from agent.domain.repositories.agent_repository import AgentRepository
from agent.domain.services.agent_publishing_service import AgentPublishingService
from agent.infrastructure.persistence.sqlalchemy_agent_repository import (
    SqlAlchemyAgentRepository,
)


class AgentContainer:
    """Dependency Container for Agent Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._agent_repository: AgentRepository = SqlAlchemyAgentRepository(session)
        self._publishing_service = AgentPublishingService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def agent_repository(self) -> AgentRepository:
        return self._agent_repository

    @property
    def publishing_service(self) -> AgentPublishingService:
        return self._publishing_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_create_agent_handler(self) -> CreateAgentHandler:
        return CreateAgentHandler(
            agent_repository=self._agent_repository,
            unit_of_work=self._uow,
        )

    def get_update_agent_handler(self) -> UpdateAgentHandler:
        return UpdateAgentHandler(
            agent_repository=self._agent_repository,
            unit_of_work=self._uow,
        )

    def get_publish_agent_handler(self) -> PublishAgentHandler:
        return PublishAgentHandler(
            agent_repository=self._agent_repository,
            publishing_service=self._publishing_service,
            unit_of_work=self._uow,
        )

    def get_archive_agent_handler(self) -> ArchiveAgentHandler:
        return ArchiveAgentHandler(
            agent_repository=self._agent_repository,
            unit_of_work=self._uow,
        )

    def get_clone_agent_handler(self) -> CloneAgentHandler:
        return CloneAgentHandler(
            agent_repository=self._agent_repository,
            unit_of_work=self._uow,
        )

    def get_agent_handler(self) -> GetAgentHandler:
        return GetAgentHandler(
            agent_repository=self._agent_repository,
        )

    def get_list_agents_handler(self) -> ListAgentsHandler:
        return ListAgentsHandler(
            agent_repository=self._agent_repository,
        )
