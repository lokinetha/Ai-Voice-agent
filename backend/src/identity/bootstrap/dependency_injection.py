"""
Identity Bounded Context Dependency Injection Bootstrap.

Wires Infrastructure implementations to Application handlers and Domain services.
"""

from __future__ import annotations

from shared.kernel.domain_event import DomainEvent
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from identity.application.commands.authenticate_user import (
    AuthenticateUserHandler,
    TokenServicePort,
)
from identity.application.commands.refresh_token import RefreshTokenHandler
from identity.application.commands.register_user import RegisterUserHandler
from identity.application.queries.get_user import GetUserHandler
from identity.domain.repositories.user_repository import UserRepository
from identity.domain.services.authentication_service import (
    AuthenticationService,
    PasswordHasherPort,
)
from identity.infrastructure.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from identity.infrastructure.security.jwt_service import JwtService
from identity.infrastructure.security.password_hasher import PBKDF2PasswordHasher


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy 2.x implementation of UnitOfWork interface."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events: list[DomainEvent] = []

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events


class IdentityContainer:
    """Dependency Container for Identity Context services and handlers."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_secret: str = "super-secret-enterprise-jwt-key-voiceforge",
    ) -> None:
        self._session = session
        self._user_repository: UserRepository = SqlAlchemyUserRepository(session)
        self._password_hasher: PasswordHasherPort = PBKDF2PasswordHasher()
        self._token_service: TokenServicePort = JwtService(secret_key=jwt_secret)
        self._auth_service = AuthenticationService(password_hasher=self._password_hasher)
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def user_repository(self) -> UserRepository:
        return self._user_repository

    @property
    def password_hasher(self) -> PasswordHasherPort:
        return self._password_hasher

    @property
    def token_service(self) -> TokenServicePort:
        return self._token_service

    @property
    def auth_service(self) -> AuthenticationService:
        return self._auth_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_register_user_handler(self) -> RegisterUserHandler:
        return RegisterUserHandler(
            user_repository=self._user_repository,
            password_hasher=self._password_hasher,
            unit_of_work=self._uow,
        )

    def get_authenticate_user_handler(self) -> AuthenticateUserHandler:
        return AuthenticateUserHandler(
            user_repository=self._user_repository,
            auth_service=self._auth_service,
            token_service=self._token_service,
            unit_of_work=self._uow,
        )

    def get_refresh_token_handler(self) -> RefreshTokenHandler:
        return RefreshTokenHandler(
            user_repository=self._user_repository,
            token_service=self._token_service,
        )

    def get_user_handler(self) -> GetUserHandler:
        return GetUserHandler(
            user_repository=self._user_repository,
        )
