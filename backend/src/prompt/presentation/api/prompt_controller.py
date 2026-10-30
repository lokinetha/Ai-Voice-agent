"""
Thin FastAPI Prompt Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from prompt.application.commands.archive_prompt import (
    ArchivePromptCommand,
    ArchivePromptHandler,
)
from prompt.application.commands.compile_prompt import (
    CompilePromptCommand,
    CompilePromptHandler,
)
from prompt.application.commands.create_prompt import (
    CreatePromptCommand,
    CreatePromptHandler,
)
from prompt.application.commands.create_prompt_version import (
    CreatePromptVersionCommand,
    CreatePromptVersionHandler,
)
from prompt.application.commands.publish_prompt import (
    PublishPromptCommand,
    PublishPromptHandler,
)
from prompt.application.commands.update_prompt import (
    UpdatePromptCommand,
    UpdatePromptHandler,
)
from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.queries.get_prompt import (
    GetPromptHandler,
    GetPromptQuery,
)
from prompt.application.queries.get_prompt_version import (
    GetPromptVersionHandler,
    GetPromptVersionQuery,
)
from prompt.application.queries.list_prompts import (
    ListPromptsHandler,
    ListPromptsQuery,
)
from prompt.presentation.schemas.requests import (
    ArchivePromptRequest,
    CompilePromptRequest,
    CreatePromptRequest,
    CreatePromptVersionRequest,
    PublishPromptRequest,
    UpdatePromptRequest,
)
from prompt.presentation.schemas.responses import (
    PromptCompilationMetadataResponse,
    PromptConstraintResponse,
    PromptExampleResponse,
    PromptInstructionResponse,
    PromptResponse,
    PromptSectionResponse,
    PromptVersionResponse,
)

router = APIRouter(prefix="/prompts", tags=["Prompt Management"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "INVALID_STATE": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVARIANT_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


def _to_prompt_response(dto: PromptDTO) -> PromptResponse:
    comp_meta = None
    if dto.compilation_metadata is not None:
        comp_meta = PromptCompilationMetadataResponse(
            source_playbook_id=dto.compilation_metadata.source_playbook_id,
            source_playbook_version=dto.compilation_metadata.source_playbook_version,
            compiled_at=dto.compilation_metadata.compiled_at,
            template_name=dto.compilation_metadata.template_name,
            checksum=dto.compilation_metadata.checksum,
        )

    version_info = PromptVersionResponse(
        version_number=dto.version_info.version_number,
        label=dto.version_info.label,
        changelog=dto.version_info.changelog,
    )

    sections = [
        PromptSectionResponse(
            id=s.id,
            section_type=s.section_type,
            title=s.title,
            content=s.content,
            order=s.order,
            instructions=[
                PromptInstructionResponse(
                    id=inst.id,
                    text=inst.text,
                    order=inst.order,
                    is_mandatory=inst.is_mandatory,
                )
                for inst in s.instructions
            ],
        )
        for s in dto.sections
    ]

    constraints = [
        PromptConstraintResponse(
            id=c.id,
            constraint_type=c.constraint_type,
            rule_text=c.rule_text,
        )
        for c in dto.constraints
    ]

    examples = [
        PromptExampleResponse(
            id=e.id,
            user_input=e.user_input,
            ideal_response=e.ideal_response,
            context=e.context,
        )
        for e in dto.examples
    ]

    return PromptResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        name=dto.name,
        description=dto.description,
        status=dto.status,
        compiled_prompt_text=dto.compiled_prompt_text,
        version_info=version_info,
        compilation_metadata=comp_meta,
        sections=sections,
        constraints=constraints,
        examples=examples,
        version=dto.version,
        created_at=dto.created_at,
    )


@router.post(
    "",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Prompt",
)
async def create_prompt(
    request: CreatePromptRequest,
    handler: CreatePromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching CreatePromptCommand."""
    command = CreatePromptCommand(
        workspace_id=request.workspace_id,
        name=request.name,
        description=request.description,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.post(
    "/{prompt_id}/compile",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Compile Prompt from Playbook",
)
async def compile_prompt(
    prompt_id: str,
    request: CompilePromptRequest,
    handler: CompilePromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching CompilePromptCommand."""
    command = CompilePromptCommand(
        prompt_id=prompt_id,
        playbook_id=request.playbook_id,
        playbook_version=request.playbook_version,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.get(
    "/{prompt_id}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Prompt details",
)
async def get_prompt(
    prompt_id: str,
    handler: GetPromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching GetPromptQuery."""
    query = GetPromptQuery(prompt_id=prompt_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.put(
    "/{prompt_id}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Prompt metadata",
)
async def update_prompt(
    prompt_id: str,
    request: UpdatePromptRequest,
    handler: UpdatePromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching UpdatePromptCommand."""
    command = UpdatePromptCommand(
        prompt_id=prompt_id,
        name=request.name,
        description=request.description,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.post(
    "/{prompt_id}/publish",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish Prompt",
)
async def publish_prompt(
    prompt_id: str,
    request: PublishPromptRequest,
    handler: PublishPromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching PublishPromptCommand."""
    command = PublishPromptCommand(
        prompt_id=prompt_id,
        label=request.label,
        changelog=request.changelog,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.post(
    "/{prompt_id}/archive",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive Prompt",
)
async def archive_prompt(
    prompt_id: str,
    request: ArchivePromptRequest,
    handler: ArchivePromptHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching ArchivePromptCommand."""
    command = ArchivePromptCommand(
        prompt_id=prompt_id,
        reason=request.reason,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.post(
    "/{prompt_id}/versions",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Prompt Version snapshot",
)
async def create_prompt_version(
    prompt_id: str,
    request: CreatePromptVersionRequest,
    handler: CreatePromptVersionHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching CreatePromptVersionCommand."""
    command = CreatePromptVersionCommand(
        prompt_id=prompt_id,
        label=request.label,
        changelog=request.changelog,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.get(
    "/{prompt_id}/versions/{version_number}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific published Prompt version snapshot",
)
async def get_prompt_version(
    prompt_id: str,
    version_number: int,
    handler: GetPromptVersionHandler = Depends(),
) -> PromptResponse:
    """Endpoint dispatching GetPromptVersionQuery."""
    query = GetPromptVersionQuery(
        prompt_id=prompt_id,
        version_number=version_number,
    )
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_prompt_response(result.value)


@router.get(
    "",
    response_model=list[PromptResponse],
    status_code=status.HTTP_200_OK,
    summary="List Prompts by Workspace",
)
async def list_prompts(
    workspace_id: str,
    handler: ListPromptsHandler = Depends(),
) -> list[PromptResponse]:
    """Endpoint dispatching ListPromptsQuery."""
    query = ListPromptsQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_prompt_response(p) for p in result.value]
