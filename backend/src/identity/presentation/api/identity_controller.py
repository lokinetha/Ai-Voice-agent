"""
Thin FastAPI Identity Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from identity.application.commands.authenticate_user import (
    AuthenticateUserCommand,
    AuthenticateUserHandler,
)
from identity.application.commands.refresh_token import (
    RefreshTokenCommand,
    RefreshTokenHandler,
)
from identity.application.commands.register_user import (
    RegisterUserCommand,
    RegisterUserHandler,
)
from identity.application.queries.get_user import GetUserHandler, GetUserQuery
from identity.presentation.schemas.requests import (
    AuthenticateUserRequest,
    RefreshTokenRequest,
    RegisterUserRequest,
)
from identity.presentation.schemas.responses import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "INVALID_CREDENTIALS": status.HTTP_401_UNAUTHORIZED,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "RATE_LIMITED": status.HTTP_429_TOO_MANY_REQUESTS,
        "INVARIANT_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: RegisterUserRequest,
    handler: RegisterUserHandler = Depends(),
) -> UserResponse:
    """Endpoint dispatching RegisterUserCommand."""
    command = RegisterUserCommand(
        tenant_id=request.tenant_id,
        email=request.email,
        password=request.password,
        role=request.role,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    dto = result.value
    return UserResponse(
        id=dto.id,
        tenant_id=dto.tenant_id,
        email=dto.email,
        role=dto.role,
        created_at=dto.created_at,
        last_login=dto.last_login,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue tokens",
)
async def login(
    request: AuthenticateUserRequest,
    handler: AuthenticateUserHandler = Depends(),
) -> TokenResponse:
    """Endpoint dispatching AuthenticateUserCommand."""
    command = AuthenticateUserCommand(
        email=request.email,
        password=request.password,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    dto = result.value
    return TokenResponse(
        access_token=dto.access_token,
        refresh_token=dto.refresh_token,
        token_type=dto.token_type,
        expires_in_seconds=dto.expires_in_seconds,
        user=UserResponse(
            id=dto.user.id,
            tenant_id=dto.user.tenant_id,
            email=dto.user.email,
            role=dto.user.role,
            created_at=dto.user.created_at,
            last_login=dto.user.last_login,
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using refresh token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    handler: RefreshTokenHandler = Depends(),
) -> TokenResponse:
    """Endpoint dispatching RefreshTokenCommand."""
    command = RefreshTokenCommand(refresh_token=request.refresh_token)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    dto = result.value
    return TokenResponse(
        access_token=dto.access_token,
        refresh_token=dto.refresh_token,
        token_type=dto.token_type,
        expires_in_seconds=dto.expires_in_seconds,
        user=UserResponse(
            id=dto.user.id,
            tenant_id=dto.user.tenant_id,
            email=dto.user.email,
            role=dto.user.role,
            created_at=dto.user.created_at,
            last_login=dto.user.last_login,
        ),
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by user_id",
)
async def get_user(
    user_id: str,
    handler: GetUserHandler = Depends(),
) -> UserResponse:
    """Endpoint dispatching GetUserQuery."""
    query = GetUserQuery(user_id=user_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    dto = result.value
    return UserResponse(
        id=dto.id,
        tenant_id=dto.tenant_id,
        email=dto.email,
        role=dto.role,
        created_at=dto.created_at,
        last_login=dto.last_login,
    )
