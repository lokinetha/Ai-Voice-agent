"""
RegisterUser Command and CommandHandler.

Orchestrates new User aggregate creation and registration.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import TenantId

from identity.application.dto.user_dto import UserDTO
from identity.application.mappers.user_mapper import UserMapper
from identity.domain.factories.user_factory import UserFactory
from identity.domain.repositories.user_repository import UserRepository
from identity.domain.services.authentication_service import PasswordHasherPort
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from identity.domain.value_objects.user_role import RoleType, UserRole


@dataclass(frozen=True)
class RegisterUserCommand(Command):
    """Command requesting new User registration."""

    tenant_id: str
    email: str
    password: str
    role: str = "MEMBER"


class RegisterUserHandler(CommandHandler[RegisterUserCommand, UserDTO]):
    """Handler executing RegisterUserCommand."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasherPort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._user_repo = user_repository
        self._password_hasher = password_hasher
        self._uow = unit_of_work

    async def handle(self, command: RegisterUserCommand) -> Result[UserDTO]:
        """Execute User registration logic.

        Args:
            command: RegisterUserCommand instance.

        Returns:
            Result wrapping UserDTO on success or Error on failure.
        """
        try:
            email_vo = Email(command.email)
        except ValueError as e:
            return Result.fail(Error("VALIDATION_ERROR", str(e)))

        # 1. Check if email already registered
        existing_user = await self._user_repo.get_by_email(email_vo)
        if existing_user is not None:
            return Result.fail(Error("CONFLICT", f"User with email '{command.email}' already exists"))

        # 2. Hash password
        hashed_pw_str = self._password_hasher.hash(command.password)
        pw_hash = PasswordHash.create(hashed_pw_str)

        # 3. Parse role
        try:
            user_role = UserRole(RoleType(command.role.upper()))
        except (ValueError, KeyError):
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid role string: {command.role}"))

        # 4. Construct aggregate via factory
        tenant_id = TenantId(command.tenant_id)
        user = UserFactory.create(
            email=email_vo,
            password_hash=pw_hash,
            tenant_id=tenant_id,
            role=user_role,
        )

        # 5. Persist aggregate within transaction
        async with self._uow:
            await self._user_repo.save(user)
            await self._uow.commit()

        return Result.ok(UserMapper.to_dto(user))
