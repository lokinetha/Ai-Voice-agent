"""
SQLAlchemy 2.x Repository Implementation for User Aggregate Root.

Implements UserRepository domain interface using async SQLAlchemy sessions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shared.kernel.specification import Specification
from shared.kernel.value_objects import EntityId, TenantId, Timestamp, UserId
from sqlalchemy import DateTime, String, select
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from identity.domain.entities.user import User
from identity.domain.repositories.user_repository import UserRepository
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from identity.domain.value_objects.user_role import RoleType, UserRole


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""



class UserModel(Base):
    """SQLAlchemy ORM Model mapping 'users' table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_algorithm: Mapped[str] = mapped_column(String(50), nullable=False, default="argon2id")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="MEMBER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with active AsyncSession.

        Args:
            session: SQLAlchemy AsyncSession context.
        """
        self._session = session

    async def get_by_id(self, id: EntityId) -> User | None:
        """Retrieve User aggregate root by ID."""
        stmt = select(UserModel).where(UserModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_email(self, email: Email) -> User | None:
        """Retrieve User aggregate root by email address."""
        stmt = select(UserModel).where(UserModel.email == email.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_api_key_hash(self, key_hash: str) -> User | None:
        """Find User owning target API key hash (stub interface method)."""
        # API keys in v2 are stored in api_keys table; stub return for aggregate lookup
        return None

    async def save(self, aggregate: User) -> None:
        """Persist or update User aggregate root."""
        stmt = select(UserModel).where(UserModel.id == str(aggregate.id.value))
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = UserModel(
                id=str(aggregate.id.value),
                org_id=str(aggregate.tenant_id.value),
                email=aggregate.email.value,
                password_hash=aggregate.password_hash.hash_value,
                password_algorithm=aggregate.password_hash.algorithm,
                role=aggregate.role.value.value,
                created_at=aggregate.created_at.value,
                last_login=aggregate.last_login.value if aggregate.last_login else None,
            )
            self._session.add(model)
        else:
            existing.email = aggregate.email.value
            existing.password_hash = aggregate.password_hash.hash_value
            existing.password_algorithm = aggregate.password_hash.algorithm
            existing.role = aggregate.role.value.value
            existing.last_login = aggregate.last_login.value if aggregate.last_login else None

    async def delete(self, aggregate: User) -> None:
        """Delete User aggregate from persistence."""
        stmt = sql_delete(UserModel).where(UserModel.id == str(aggregate.id.value))
        await self._session.execute(stmt)

    async def find(self, spec: Specification[User]) -> list[User]:
        """Find User aggregates matching specification filter."""
        stmt = select(UserModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        aggregates = [self._to_aggregate(m) for m in models]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[User]) -> int:
        """Count User aggregates matching specification filter."""
        aggregates = await self.find(spec)
        return len(aggregates)

    @staticmethod
    def _to_aggregate(model: UserModel) -> User:
        """Map ORM UserModel to domain User aggregate root."""
        # Ensure timezone-aware datetimes
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        last_login_dt = model.last_login
        if last_login_dt and last_login_dt.tzinfo is None:
            last_login_dt = last_login_dt.replace(tzinfo=UTC)

        return User(
            id=UserId(model.id),
            email=Email(model.email),
            password_hash=PasswordHash(hash_value=model.password_hash, algorithm=model.password_algorithm),
            role=UserRole(RoleType(model.role)),
            tenant_id=TenantId(model.org_id),
            created_at=Timestamp(created_at_dt),
            last_login=Timestamp(last_login_dt) if last_login_dt else None,
        )
