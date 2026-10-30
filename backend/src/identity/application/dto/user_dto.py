"""
User Data Transfer Objects (DTOs) for Identity Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserDTO:
    """Data Transfer Object representing a User."""

    id: str
    tenant_id: str
    email: str
    role: str
    created_at: datetime
    last_login: datetime | None


@dataclass(frozen=True)
class TokenResponseDTO:
    """Data Transfer Object representing authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in_seconds: int
    user: UserDTO
