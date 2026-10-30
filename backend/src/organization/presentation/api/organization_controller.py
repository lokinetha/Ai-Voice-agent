"""
Thin FastAPI Organization Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from shared.kernel.result import Error

from organization.application.commands.change_plan import (
    ChangePlanCommand,
    ChangePlanHandler,
)
from organization.application.commands.create_organization import (
    CreateOrganizationCommand,
    CreateOrganizationHandler,
)
from organization.application.commands.create_workspace import (
    CreateWorkspaceCommand,
    CreateWorkspaceHandler,
)
from organization.application.dto.organization_dto import (
    OrganizationDTO,
)
from organization.application.queries.get_organization import (
    GetOrganizationHandler,
    GetOrganizationQuery,
)
from organization.application.queries.get_workspaces import (
    GetWorkspacesHandler,
    GetWorkspacesQuery,
)
from organization.presentation.schemas.requests import (
    ChangePlanRequest,
    CreateOrganizationRequest,
    CreateWorkspaceRequest,
)
from organization.presentation.schemas.responses import (
    OrganizationResponse,
    PlanResponse,
    WorkspaceResponse,
)

router = APIRouter(prefix="/org", tags=["Organization Management"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "LIMIT_EXCEEDED": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVARIANT_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


def _to_org_response(dto: OrganizationDTO) -> OrganizationResponse:
    return OrganizationResponse(
        id=dto.id,
        tenant_id=dto.tenant_id,
        name=dto.name,
        plan=PlanResponse(
            tier=dto.plan.tier,
            max_agents=dto.plan.max_agents,
            max_minutes_per_month=dto.plan.max_minutes_per_month,
            max_kb_documents=dto.plan.max_kb_documents,
            max_workspaces=dto.plan.max_workspaces,
            price_cents=dto.plan.price_cents,
            currency=dto.plan.currency,
        ),
        billing_email=dto.billing_email,
        workspaces=[
            WorkspaceResponse(
                id=w.id, name=w.name, status=w.status, created_at=w.created_at
            )
            for w in dto.workspaces
        ],
        created_at=dto.created_at,
    )


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Organization",
)
async def create_organization(
    request: CreateOrganizationRequest,
    handler: CreateOrganizationHandler = Depends(),
) -> OrganizationResponse:
    """Endpoint dispatching CreateOrganizationCommand."""
    command = CreateOrganizationCommand(
        name=request.name,
        billing_email=request.billing_email,
        tenant_id=request.tenant_id,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_org_response(result.value)


@router.get(
    "/me",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active tenant Organization details",
)
async def get_organization(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    handler: GetOrganizationHandler = Depends(),
) -> OrganizationResponse:
    """Endpoint dispatching GetOrganizationQuery."""
    query = GetOrganizationQuery(tenant_id=x_tenant_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_org_response(result.value)


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Workspace within Organization",
)
async def create_workspace(
    request: CreateWorkspaceRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    handler: CreateWorkspaceHandler = Depends(),
) -> WorkspaceResponse:
    """Endpoint dispatching CreateWorkspaceCommand."""
    command = CreateWorkspaceCommand(
        tenant_id=x_tenant_id,
        workspace_name=request.workspace_name,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    ws_dto = result.value
    return WorkspaceResponse(
        id=ws_dto.id,
        name=ws_dto.name,
        status=ws_dto.status,
        created_at=ws_dto.created_at,
    )


@router.get(
    "/workspaces",
    response_model=list[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Workspaces for Organization",
)
async def get_workspaces(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    handler: GetWorkspacesHandler = Depends(),
) -> list[WorkspaceResponse]:
    """Endpoint dispatching GetWorkspacesQuery."""
    query = GetWorkspacesQuery(tenant_id=x_tenant_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return [
        WorkspaceResponse(
            id=w.id, name=w.name, status=w.status, created_at=w.created_at
        )
        for w in result.value
    ]


@router.post(
    "/plan",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Organization subscription plan",
)
async def change_plan(
    request: ChangePlanRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    handler: ChangePlanHandler = Depends(),
) -> OrganizationResponse:
    """Endpoint dispatching ChangePlanCommand."""
    command = ChangePlanCommand(
        tenant_id=x_tenant_id,
        target_plan_tier=request.target_plan_tier,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_org_response(result.value)
