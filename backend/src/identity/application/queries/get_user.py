"""
GetUser Query and QueryHandler.

Side-effect-free query retrieving User details by ID.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import UserId

from identity.application.dto.user_dto import UserDTO
from identity.application.mappers.user_mapper import UserMapper
from identity.domain.repositories.user_repository import UserRepository


@dataclass(frozen=True)
class GetUserQuery(Query):
    """Query requesting user detail by user_id."""

    user_id: str


class GetUserHandler(QueryHandler[GetUserQuery, UserDTO]):
    """Handler executing GetUserQuery."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repo = user_repository

    async def handle(self, query: GetUserQuery) -> Result[UserDTO]:
        """Execute GetUserQuery.

        Args:
            query: GetUserQuery instance.

        Returns:
            Result wrapping UserDTO if found, or NOT_FOUND Error.
        """
        if not query.user_id:
            return Result.fail(Error("VALIDATION_ERROR", "User ID cannot be empty"))

        user = await self._user_repo.get_by_id(UserId(query.user_id))
        if user is None:
            return Result.fail(Error("NOT_FOUND", f"User with ID '{query.user_id}' not found"))

        return Result.ok(UserMapper.to_dto(user))
