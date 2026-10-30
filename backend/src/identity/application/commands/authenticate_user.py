"""
AuthenticateUser Command and CommandHandler.

Orchestrates user credential validation and JWT token issuance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork

from identity.application.dto.user_dto import TokenResponseDTO
from identity.application.mappers.user_mapper import UserMapper
from identity.domain.repositories.user_repository import UserRepository
from identity.domain.services.authentication_service import AuthenticationService
from identity.domain.value_objects.email import Email


class TokenServicePort(Protocol):
    """Protocol for JWT Token Service in Application layer."""

    def create_token_pair(
        self, user_id: str, tenant_id: str, role: str
    ) -> tuple[str, str, int]:
        """Generate (access_token, refresh_token, expires_in_seconds)."""
        ...

    def verify_refresh_token(self, token: str) -> dict[str, str]:
        """Verify refresh token and return payload containing user_id."""
        ...


@dataclass(frozen=True)
class AuthenticateUserCommand(Command):
    """Command requesting user authentication."""

    email: str
    password: str


class AuthenticateUserHandler(CommandHandler[AuthenticateUserCommand, TokenResponseDTO]):
    """Handler executing AuthenticateUserCommand."""

    def __init__(
        self,
        user_repository: UserRepository,
        auth_service: AuthenticationService,
        token_service: TokenServicePort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._user_repo = user_repository
        self._auth_service = auth_service
        self._token_service = token_service
        self._uow = unit_of_work

    async def handle(
        self, command: AuthenticateUserCommand
    ) -> Result[TokenResponseDTO]:
        """Execute user authentication and token creation.

        Args:
            command: AuthenticateUserCommand instance.

        Returns:
            Result wrapping TokenResponseDTO on success, or Error on failure.
        """
        try:
            email_vo = Email(command.email)
        except ValueError:
            return Result.fail(Error("INVALID_CREDENTIALS", "Invalid email or password"))

        # 1. Fetch user by email
        user = await self._user_repo.get_by_email(email_vo)
        if user is None:
            return Result.fail(Error("INVALID_CREDENTIALS", "Invalid email or password"))

        # 2. Authenticate via Domain Service
        auth_result = self._auth_service.authenticate(user, command.password)
        if auth_result.is_failure:
            return Result.fail(auth_result.error)

        # 3. Persist login timestamp state change
        async with self._uow:
            await self._user_repo.save(user)
            await self._uow.commit()

        # 4. Generate JWT tokens
        access_token, refresh_token, expires_in = self._token_service.create_token_pair(
            user_id=str(user.id.value),
            tenant_id=str(user.tenant_id.value),
            role=user.role.value.value,
        )

        dto = TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in_seconds=expires_in,
            user=UserMapper.to_dto(user),
        )
        return Result.ok(dto)
