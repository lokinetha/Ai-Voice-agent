"""
Pydantic Request Schemas for Identity Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterUserRequest(BaseModel):
    """HTTP Request schema for registering a new user."""

    tenant_id: str = Field(..., description="Organization or Tenant ID boundary", examples=["tenant-123"])
    email: EmailStr = Field(..., description="User valid email address", examples=["user@enterprise.com"])
    password: str = Field(..., min_length=8, description="User plain text password", examples=["SecureP@ss123"])
    role: str = Field(default="MEMBER", description="User role (OWNER, ADMIN, MEMBER, VIEWER)", examples=["MEMBER"])


class AuthenticateUserRequest(BaseModel):
    """HTTP Request schema for authenticating user credentials."""

    email: EmailStr = Field(..., description="Registered user email", examples=["user@enterprise.com"])
    password: str = Field(..., description="User plain text password", examples=["SecureP@ss123"])


class RefreshTokenRequest(BaseModel):
    """HTTP Request schema for refreshing JWT access tokens."""

    refresh_token: str = Field(..., description="Valid JWT refresh token", examples=["eyJhbGciOiJIUzI1Ni..."])
