"""
RefreshToken Command and CommandHandler.

Orchestrates validation of refresh tokens and issuance of new JWT access/refresh token pairs.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import UserId

from identity.application.commands.authenticate_user import TokenServicePort
from identity.application.dto.user_dto import TokenResponseDTO
from identity.application.mappers.user_mapper import UserMapper
from identity.domain.repositories.user_repository import UserRepository


@dataclass(frozen=True)
class RefreshTokenCommand(Command):
    """Command requesting token refresh using a valid refresh token."""

    refresh_token: str


class RefreshTokenHandler(CommandHandler[RefreshTokenCommand, TokenResponseDTO]):
    """Handler executing RefreshTokenCommand."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenServicePort,
    ) -> None:
        self._user_repo = user_repository
        self._token_service = token_service

    async def handle(self, command: RefreshTokenCommand) -> Result[TokenResponseDTO]:
        """Execute refresh token verification and issue new tokens.

        Args:
            command: RefreshTokenCommand instance.

        Returns:
            Result wrapping new TokenResponseDTO on success, or Error on failure.
        """
        if not command.refresh_token:
            return Result.fail(Error("VALIDATION_ERROR", "Refresh token cannot be empty"))

        try:
            payload = self._token_service.verify_refresh_token(command.refresh_token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                return Result.fail(Error("UNAUTHORIZED", "Invalid token payload"))
        except Exception as e:
            return Result.fail(Error("UNAUTHORIZED", f"Invalid or expired refresh token: {e}"))

        # Fetch user
        user = await self._user_repo.get_by_id(UserId(user_id_str))
        if user is None:
            return Result.fail(Error("NOT_FOUND", "User not found"))

        # Issue new token pair
        access_token, new_refresh_token, expires_in = self._token_service.create_token_pair(
            user_id=str(user.id.value),
            tenant_id=str(user.tenant_id.value),
            role=user.role.value.value,
        )

        dto = TokenResponseDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in_seconds=expires_in,
            user=UserMapper.to_dto(user),
        )
        return Result.ok(dto)
