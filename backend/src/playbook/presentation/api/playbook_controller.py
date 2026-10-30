"""
Thin FastAPI Playbook Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from playbook.application.commands.archive_playbook import (
    ArchivePlaybookCommand,
    ArchivePlaybookHandler,
)
from playbook.application.commands.create_playbook import (
    CreatePlaybookCommand,
    CreatePlaybookHandler,
)
from playbook.application.commands.create_playbook_version import (
    CreatePlaybookVersionCommand,
    CreatePlaybookVersionHandler,
)
from playbook.application.commands.publish_playbook import (
    PublishPlaybookCommand,
    PublishPlaybookHandler,
)
from playbook.application.commands.update_playbook import (
    UpdatePlaybookCommand,
    UpdatePlaybookHandler,
)
from playbook.application.dto.playbook_dto import PlaybookDTO
from playbook.application.queries.get_playbook import (
    GetPlaybookHandler,
    GetPlaybookQuery,
)
from playbook.application.queries.get_playbook_version import (
    GetPlaybookVersionHandler,
    GetPlaybookVersionQuery,
)
from playbook.application.queries.list_playbooks import (
    ListPlaybooksHandler,
    ListPlaybooksQuery,
)
from playbook.presentation.schemas.requests import (
    ArchivePlaybookRequest,
    CreatePlaybookRequest,
    CreatePlaybookVersionRequest,
    PublishPlaybookRequest,
    UpdatePlaybookRequest,
)
from playbook.presentation.schemas.responses import (
    CommunicationStyleResponse,
    ExampleResponse,
    GoalResponse,
    ObjectionResponse,
    PersonaResponse,
    PlaybookResponse,
    PlaybookVersionResponse,
    RuleResponse,
    StageResponse,
    SuccessCriteriaResponse,
    TransitionResponse,
)

router = APIRouter(prefix="/playbooks", tags=["Playbook Management"])


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


def _to_playbook_response(dto: PlaybookDTO) -> PlaybookResponse:
    persona = None
    if dto.persona is not None:
        persona = PersonaResponse(
            name=dto.persona.name,
            role=dto.persona.role,
            description=dto.persona.description,
            industry=dto.persona.industry,
        )

    comm_style = None
    if dto.communication_style is not None:
        comm_style = CommunicationStyleResponse(
            tone=dto.communication_style.tone,
            formality=dto.communication_style.formality,
            pacing=dto.communication_style.pacing,
            vocabulary_level=dto.communication_style.vocabulary_level,
            use_filler_words=dto.communication_style.use_filler_words,
        )

    criteria = None
    if dto.success_criteria is not None:
        criteria = SuccessCriteriaResponse(
            primary_metric=dto.success_criteria.primary_metric,
            target_value=dto.success_criteria.target_value,
            secondary_metrics=list(dto.success_criteria.secondary_metrics),
            description=dto.success_criteria.description,
        )

    version_info = PlaybookVersionResponse(
        version_number=dto.version_info.version_number,
        label=dto.version_info.label,
        changelog=dto.version_info.changelog,
    )

    goals = [
        GoalResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            priority=g.priority,
            is_mandatory=g.is_mandatory,
        )
        for g in dto.goals
    ]

    stages = [
        StageResponse(
            id=s.id,
            name=s.name,
            order=s.order,
            description=s.description,
            goals=[
                GoalResponse(
                    id=g.id,
                    name=g.name,
                    description=g.description,
                    priority=g.priority,
                    is_mandatory=g.is_mandatory,
                )
                for g in s.goals
            ],
        )
        for s in dto.stages
    ]

    rules = [
        RuleResponse(
            id=r.id,
            name=r.name,
            condition=r.condition,
            action=r.action,
            is_strict=r.is_strict,
        )
        for r in dto.rules
    ]

    objections = [
        ObjectionResponse(
            id=o.id,
            trigger_phrase=o.trigger_phrase,
            objection_category=o.objection_category,
            response_strategy=o.response_strategy,
            recommended_response=o.recommended_response,
        )
        for o in dto.objections
    ]

    examples = [
        ExampleResponse(
            id=e.id,
            scenario=e.scenario,
            user_input=e.user_input,
            ideal_response=e.ideal_response,
            explanation=e.explanation,
        )
        for e in dto.examples
    ]

    transitions = [
        TransitionResponse(
            id=t.id,
            from_stage_id=t.from_stage_id,
            to_stage_id=t.to_stage_id,
            condition=t.condition,
        )
        for t in dto.transitions
    ]

    return PlaybookResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        name=dto.name,
        description=dto.description,
        status=dto.status,
        version_info=version_info,
        persona=persona,
        communication_style=comm_style,
        success_criteria=criteria,
        goals=goals,
        stages=stages,
        rules=rules,
        objections=objections,
        examples=examples,
        transitions=transitions,
        version=dto.version,
        created_at=dto.created_at,
    )


@router.post(
    "",
    response_model=PlaybookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Playbook",
)
async def create_playbook(
    request: CreatePlaybookRequest,
    handler: CreatePlaybookHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching CreatePlaybookCommand."""
    command = CreatePlaybookCommand(
        workspace_id=request.workspace_id,
        name=request.name,
        description=request.description,
        persona_name=request.persona_name,
        persona_role=request.persona_role,
        persona_description=request.persona_description,
        persona_industry=request.persona_industry,
        tone=request.tone,
        formality=request.formality,
        pacing=request.pacing,
        primary_metric=request.primary_metric,
        target_value=request.target_value,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.get(
    "/{playbook_id}",
    response_model=PlaybookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Playbook details",
)
async def get_playbook(
    playbook_id: str,
    handler: GetPlaybookHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching GetPlaybookQuery."""
    query = GetPlaybookQuery(playbook_id=playbook_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.put(
    "/{playbook_id}",
    response_model=PlaybookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Playbook metadata",
)
async def update_playbook(
    playbook_id: str,
    request: UpdatePlaybookRequest,
    handler: UpdatePlaybookHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching UpdatePlaybookCommand."""
    command = UpdatePlaybookCommand(
        playbook_id=playbook_id,
        name=request.name,
        description=request.description,
        persona_name=request.persona_name,
        persona_role=request.persona_role,
        persona_description=request.persona_description,
        persona_industry=request.persona_industry,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.post(
    "/{playbook_id}/publish",
    response_model=PlaybookResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish Playbook",
)
async def publish_playbook(
    playbook_id: str,
    request: PublishPlaybookRequest,
    handler: PublishPlaybookHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching PublishPlaybookCommand."""
    command = PublishPlaybookCommand(
        playbook_id=playbook_id,
        label=request.label,
        changelog=request.changelog,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.post(
    "/{playbook_id}/archive",
    response_model=PlaybookResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive Playbook",
)
async def archive_playbook(
    playbook_id: str,
    request: ArchivePlaybookRequest,
    handler: ArchivePlaybookHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching ArchivePlaybookCommand."""
    command = ArchivePlaybookCommand(
        playbook_id=playbook_id,
        reason=request.reason,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.post(
    "/{playbook_id}/versions",
    response_model=PlaybookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Playbook Version snapshot",
)
async def create_playbook_version(
    playbook_id: str,
    request: CreatePlaybookVersionRequest,
    handler: CreatePlaybookVersionHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching CreatePlaybookVersionCommand."""
    command = CreatePlaybookVersionCommand(
        playbook_id=playbook_id,
        label=request.label,
        changelog=request.changelog,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.get(
    "/{playbook_id}/versions/{version_number}",
    response_model=PlaybookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific published Playbook version snapshot",
)
async def get_playbook_version(
    playbook_id: str,
    version_number: int,
    handler: GetPlaybookVersionHandler = Depends(),
) -> PlaybookResponse:
    """Endpoint dispatching GetPlaybookVersionQuery."""
    query = GetPlaybookVersionQuery(
        playbook_id=playbook_id,
        version_number=version_number,
    )
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_playbook_response(result.value)


@router.get(
    "",
    response_model=list[PlaybookResponse],
    status_code=status.HTTP_200_OK,
    summary="List Playbooks by Workspace",
)
async def list_playbooks(
    workspace_id: str,
    handler: ListPlaybooksHandler = Depends(),
) -> list[PlaybookResponse]:
    """Endpoint dispatching ListPlaybooksQuery."""
    query = ListPlaybooksQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_playbook_response(pb) for pb in result.value]
