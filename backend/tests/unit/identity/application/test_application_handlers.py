"""
Unit tests for Identity Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest

from identity.application.commands.authenticate_user import (
    AuthenticateUserCommand,
    AuthenticateUserHandler,
)
from identity.application.commands.refresh_token import (
    RefreshTokenCommand,
    RefreshTokenHandler,
)
from identity.application.commands.register_user import (
    RegisterUserCommand,
    RegisterUserHandler,
)
from identity.application.queries.get_user import GetUserHandler, GetUserQuery
from identity.domain.entities.user import User
from identity.domain.repositories.user_repository import UserRepository
from identity.domain.services.authentication_service import (
    AuthenticationService,
    PasswordHasherPort,
)
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    async def get_by_id(self, id: EntityId) -> User | None:
        return self.users.get(str(id.value))

    async def get_by_email(self, email: Email) -> User | None:
        for u in self.users.values():
            if u.email == email:
                return u
        return None

    async def get_by_api_key_hash(self, key_hash: str) -> User | None:
        return None

    async def save(self, aggregate: User) -> None:
        self.users[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: User) -> None:
        self.users.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[User]) -> list[User]:
        return [u for u in self.users.values() if spec.is_satisfied_by(u)]

    async def count(self, spec: Specification[User]) -> int:
        return len(await self.find(spec))


class DummyHasher(PasswordHasherPort):
    def hash(self, plain_password: str) -> str:
        return f"hashed_{plain_password}"

    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        return password_hash.hash_value == f"hashed_{plain_password}"


class DummyTokenService:
    def create_token_pair(self, user_id: str, tenant_id: str, role: str) -> tuple[str, str, int]:
        return f"access_{user_id}", f"refresh_{user_id}", 3600

    def verify_refresh_token(self, token: str) -> dict[str, str]:
        if not token.startswith("refresh_"):
            raise ValueError("Invalid refresh token")
        user_id = token.replace("refresh_", "")
        return {"sub": user_id, "type": "refresh"}


class DummyUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> DummyUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestIdentityApplicationHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryUserRepository()
        self.hasher = DummyHasher()
        self.uow = DummyUnitOfWork()
        self.tokens = DummyTokenService()
        self.auth_service = AuthenticationService(self.hasher)

    def test_register_user_success(self) -> None:
        async def run() -> None:
            handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            cmd = RegisterUserCommand(
                tenant_id="tenant-1",
                email="newuser@enterprise.com",
                password="secret_password",
                role="MEMBER",
            )
            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.email, "newuser@enterprise.com")
            self.assertTrue(self.uow.committed)

        asyncio.run(run())

    def test_register_user_conflict(self) -> None:
        async def run() -> None:
            handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            cmd = RegisterUserCommand(
                tenant_id="tenant-1",
                email="existing@enterprise.com",
                password="secret_password",
            )
            res1 = await handler.handle(cmd)
            self.assertTrue(res1.is_success)

            # Second registration attempt with same email
            res2 = await handler.handle(cmd)
            self.assertTrue(res2.is_failure)
            self.assertEqual(res2.error.code, "CONFLICT")

        asyncio.run(run())

    def test_authenticate_user_success(self) -> None:
        async def run() -> None:
            reg_handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            await reg_handler.handle(
                RegisterUserCommand("t1", "authuser@enterprise.com", "my_pass")
            )

            auth_handler = AuthenticateUserHandler(
                self.repo, self.auth_service, self.tokens, self.uow
            )
            res = await auth_handler.handle(
                AuthenticateUserCommand("authuser@enterprise.com", "my_pass")
            )
            self.assertTrue(res.is_success)
            self.assertIsNotNone(res.value.access_token)
            self.assertEqual(res.value.user.email, "authuser@enterprise.com")

        asyncio.run(run())

    def test_authenticate_user_invalid_password(self) -> None:
        async def run() -> None:
            reg_handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            await reg_handler.handle(
                RegisterUserCommand("t1", "authuser2@enterprise.com", "my_pass")
            )

            auth_handler = AuthenticateUserHandler(
                self.repo, self.auth_service, self.tokens, self.uow
            )
            res = await auth_handler.handle(
                AuthenticateUserCommand("authuser2@enterprise.com", "wrong_pass")
            )
            self.assertTrue(res.is_failure)
            self.assertEqual(res.error.code, "INVALID_CREDENTIALS")

        asyncio.run(run())

    def test_refresh_token_success(self) -> None:
        async def run() -> None:
            reg_handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            reg_res = await reg_handler.handle(
                RegisterUserCommand("t1", "refreshuser@enterprise.com", "pass")
            )
            user_id = reg_res.value.id

            refresh_handler = RefreshTokenHandler(self.repo, self.tokens)
            res = await refresh_handler.handle(RefreshTokenCommand(f"refresh_{user_id}"))
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.user.id, user_id)

        asyncio.run(run())

    def test_get_user_query_success(self) -> None:
        async def run() -> None:
            reg_handler = RegisterUserHandler(self.repo, self.hasher, self.uow)
            reg_res = await reg_handler.handle(
                RegisterUserCommand("t1", "queryuser@enterprise.com", "pass")
            )
            user_id = reg_res.value.id

            get_handler = GetUserHandler(self.repo)
            res = await get_handler.handle(GetUserQuery(user_id=user_id))
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.email, "queryuser@enterprise.com")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
