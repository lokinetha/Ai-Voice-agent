"""
UserRepository Domain Interface for Identity Context.

Extends generic Repository interface for User aggregate root persistence operations.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import UserId

from identity.domain.entities.user import User
from identity.domain.value_objects.email import Email


class UserRepository(Repository[User, UserId]):
    """Domain Repository Interface for User Aggregate Root."""

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        """Find User aggregate by unique email address.

        Args:
            email: Email value object.

        Returns:
            User aggregate root instance if found, or None.
        """
        ...

    @abstractmethod
    async def get_by_api_key_hash(self, key_hash: str) -> User | None:
        """Find User aggregate owning the provided API key hash.

        Args:
            key_hash: Hashed secret key string.

        Returns:
            User aggregate root instance if found, or None.
        """
        ...
