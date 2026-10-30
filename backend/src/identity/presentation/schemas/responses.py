"""
Pydantic Response Schemas for Identity Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """HTTP Response schema representing a User."""

    id: str = Field(..., description="Unique UserId")
    tenant_id: str = Field(..., description="Tenant organization ID")
    email: str = Field(..., description="User email address")
    role: str = Field(..., description="User access role")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    last_login: datetime | None = Field(default=None, description="UTC last login timestamp")


class TokenResponse(BaseModel):
    """HTTP Response schema for authentication token issuance."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in_seconds: int = Field(..., description="Access token expiration window in seconds")
    user: UserResponse = Field(..., description="Authenticated User profile")
