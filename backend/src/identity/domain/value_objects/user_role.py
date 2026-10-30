"""
UserRole Value Object for Identity Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class RoleType(StrEnum):
    """Enumeration of system role authorization levels."""

    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    MEMBER = "MEMBER"
    WORKSPACE_MANAGER = "WORKSPACE_MANAGER"
    AGENT_DEVELOPER = "AGENT_DEVELOPER"
    ANALYST = "ANALYST"
    READ_ONLY = "READ_ONLY"


@dataclass(frozen=True)
class UserRole(ValueObject):
    """UserRole Value Object encapsulating system authorization role."""

    value: RoleType

    def _validate(self) -> None:
        if not isinstance(self.value, RoleType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", RoleType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid UserRole string: {self.value}") from err
            else:
                raise ValueError(f"UserRole value must be a RoleType enum, got: {type(self.value)}")

    @classmethod
    def org_admin(cls) -> UserRole:
        return cls(value=RoleType.ORG_ADMIN)

    @classmethod
    def admin(cls) -> UserRole:
        return cls(value=RoleType.ADMIN)

    @classmethod
    def owner(cls) -> UserRole:
        return cls(value=RoleType.OWNER)

    @classmethod
    def member(cls) -> UserRole:
        return cls(value=RoleType.MEMBER)

    @classmethod
    def agent_developer(cls) -> UserRole:
        return cls(value=RoleType.AGENT_DEVELOPER)

    @classmethod
    def read_only(cls) -> UserRole:
        return cls(value=RoleType.READ_ONLY)
