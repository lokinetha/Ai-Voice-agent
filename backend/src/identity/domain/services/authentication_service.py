"""
AuthenticationService Domain Service for Identity Bounded Context.

Coordinates domain validation logic during user authentication workflows.
"""

from __future__ import annotations

from typing import Protocol

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import Timestamp

from identity.domain.entities.user import User
from identity.domain.value_objects.password_hash import PasswordHash


class PasswordHasherPort(Protocol):
    """Protocol for password hashing and verification strategy."""

    def hash(self, plain_password: str) -> str:
        """Generate secure password hash string from plain text."""
        ...

    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        """Verify plain text password against stored PasswordHash."""
        ...


class AuthenticationService(DomainService):
    """Domain Service for validating user authentication attempts and updating aggregate state."""

    def __init__(self, password_hasher: PasswordHasherPort) -> None:
        """Initialize AuthenticationService with password hasher abstraction.

        Args:
            password_hasher: Implementation of PasswordHasherPort.
        """
        self._password_hasher = password_hasher

    def authenticate(
        self, user: User, plain_password: str, login_time: Timestamp | None = None
    ) -> Result[User]:
        """Authenticate user credentials and record login timestamp on success.

        Args:
            user: User Aggregate Root instance.
            plain_password: Plain text password provided during authentication.
            login_time: Optional explicit timestamp of authentication event.

        Returns:
            Result wrapping authenticated User on success, or INVALID_CREDENTIALS Error.
        """
        if not self._password_hasher.verify(plain_password, user.password_hash):
            return Result.fail(Error("INVALID_CREDENTIALS", "Invalid email or password"))

        user.record_login(login_time)
        return Result.ok(user)
