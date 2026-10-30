"""
UserRegistered Domain Event.

Raised when a new User aggregate is registered in the system.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    """Domain Event published upon successful User aggregate registration.

    Attributes:
        user_id: String representation of registered UserId.
        email: Registered user email string.
        role: Initial assigned role string.
    """

    user_id: str = ""
    email: str = ""
    role: str = ""
