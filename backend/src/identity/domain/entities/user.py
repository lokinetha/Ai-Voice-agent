"""
User Aggregate Root for Identity Bounded Context.

Central Aggregate Root managing user profile, password hash, role assignments,
API keys, and login tracking.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId, TenantId, Timestamp, UserId

from identity.domain.entities.api_key import ApiKey
from identity.domain.events.user_role_changed import UserRoleChanged
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from identity.domain.value_objects.user_role import UserRole


class User(AggregateRoot[UserId]):
    """User Aggregate Root.

    Enforces invariants regarding credentials, access roles, and API keys.
    """

    def __init__(
        self,
        id: UserId,
        email: Email,
        password_hash: PasswordHash,
        role: UserRole,
        tenant_id: TenantId,
        created_at: Timestamp | None = None,
        last_login: Timestamp | None = None,
        api_keys: Sequence[ApiKey] = (),
        version: int = 0,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._tenant_id = tenant_id
        self._last_login = last_login
        self._api_keys: dict[EntityId, ApiKey] = {key.id: key for key in api_keys}

    @property
    def email(self) -> Email:
        """Get user email value object."""
        return self._email

    @property
    def password_hash(self) -> PasswordHash:
        """Get password hash value object."""
        return self._password_hash

    @property
    def role(self) -> UserRole:
        """Get user role value object."""
        return self._role

    @property
    def tenant_id(self) -> TenantId:
        """Get user tenant identifier."""
        return self._tenant_id

    @property
    def last_login(self) -> Timestamp | None:
        """Get last successful login timestamp."""
        return self._last_login

    @property
    def api_keys(self) -> tuple[ApiKey, ...]:
        """Get immutable view of associated API keys."""
        return tuple(self._api_keys.values())

    def update_password(self, new_password_hash: PasswordHash) -> Result[None]:
        """Update user's password hash.

        Args:
            new_password_hash: New PasswordHash instance.

        Returns:
            Result indicating success.
        """
        if new_password_hash == self._password_hash:
            return Result.fail(Error("INVALID_PASSWORD", "New password cannot be identical to current password"))

        self._password_hash = new_password_hash
        return Result.ok(None)

    def update_role(self, new_role: UserRole) -> Result[None]:
        """Update user role and raise UserRoleChanged domain event.

        Args:
            new_role: UserRole to assign.

        Returns:
            Result indicating success.
        """
        if new_role == self._role:
            return Result.ok(None)

        old_role_str = self._role.value.value
        self._role = new_role

        self._raise_event(
            UserRoleChanged(
                user_id=str(self.id.value),
                tenant_id=str(self.tenant_id.value),
                old_role=old_role_str,
                new_role=new_role.value.value,
            )
        )
        return Result.ok(None)

    def record_login(self, login_timestamp: Timestamp | None = None) -> None:
        """Record successful authentication event.

        Args:
            login_timestamp: UTC timestamp of login event.
        """
        self._last_login = login_timestamp or Timestamp.now()

    def add_api_key(self, api_key: ApiKey) -> Result[None]:
        """Associate a new ApiKey entity with the User aggregate.

        Args:
            api_key: ApiKey entity to associate.

        Returns:
            Result indicating success or failure if already exists.
        """
        if api_key.id in self._api_keys:
            return Result.fail(Error("DUPLICATE_KEY", f"ApiKey {api_key.id.value} already exists"))

        self._api_keys[api_key.id] = api_key
        return Result.ok(None)

    def revoke_api_key(self, api_key_id: EntityId) -> Result[None]:
        """Revoke and remove an ApiKey entity from User aggregate.

        Args:
            api_key_id: EntityId of ApiKey to remove.

        Returns:
            Result indicating success or NOT_FOUND error.
        """
        if api_key_id not in self._api_keys:
            return Result.fail(Error("NOT_FOUND", f"ApiKey {api_key_id.value} not found"))

        del self._api_keys[api_key_id]
        return Result.ok(None)
