"""
UserMapper for mapping between Domain Aggregate Roots and Application DTOs.
"""

from __future__ import annotations

from identity.application.dto.user_dto import UserDTO
from identity.domain.entities.user import User


class UserMapper:
    """Static mapper for User Aggregate Root ↔ UserDTO conversion."""

    @staticmethod
    def to_dto(user: User) -> UserDTO:
        """Map User aggregate root to UserDTO.

        Args:
            user: Domain User aggregate root.

        Returns:
            UserDTO instance.
        """
        return UserDTO(
            id=str(user.id.value),
            tenant_id=str(user.tenant_id.value),
            email=user.email.value,
            role=user.role.value.value,
            created_at=user.created_at.value,
            last_login=user.last_login.value if user.last_login else None,
        )
