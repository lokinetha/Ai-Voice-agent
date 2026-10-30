"""
UserRoleChanged Domain Event.

Raised when a User's authorization role is updated.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class UserRoleChanged(DomainEvent):
    """Domain Event published when a User aggregate's role is updated.

    Attributes:
        user_id: String representation of target UserId.
        old_role: Previous role string.
        new_role: Updated role string.
    """

    user_id: str = ""
    old_role: str = ""
    new_role: str = ""
