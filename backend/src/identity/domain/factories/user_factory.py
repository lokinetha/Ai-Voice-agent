"""
UserFactory for Identity Bounded Context.

Encapsulates the creation logic of User Aggregate Roots, ensuring proper default
assignments and domain event registration upon creation.
"""

from __future__ import annotations

from shared.kernel.value_objects import TenantId, UserId

from identity.domain.entities.user import User
from identity.domain.events.user_registered import UserRegistered
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from identity.domain.value_objects.user_role import UserRole


class UserFactory:
    """Factory for creating new User Aggregate Roots."""

    @classmethod
    def create(
        self,
        email: Email,
        password_hash: PasswordHash,
        tenant_id: TenantId,
        role: UserRole | None = None,
        user_id: UserId | None = None,
    ) -> User:
        """Create and initialize a new User aggregate root.

        Args:
            email: User Email value object.
            password_hash: PasswordHash value object.
            tenant_id: TenantId organization boundary identifier.
            role: Optional UserRole (defaults to MEMBER if None).
            user_id: Optional explicit UserId (generates UUID4 if None).

        Returns:
            Initialized User Aggregate Root with recorded UserRegistered domain event.
        """
        id_val = user_id or UserId()
        user_role = role or UserRole.member()

        user = User(
            id=id_val,
            email=email,
            password_hash=password_hash,
            role=user_role,
            tenant_id=tenant_id,
        )

        user._raise_event(
            UserRegistered(
                user_id=str(user.id.value),
                tenant_id=str(tenant_id.value),
                email=email.value,
                role=user_role.value.value,
            )
        )

        return user
