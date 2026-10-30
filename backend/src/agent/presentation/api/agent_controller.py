"""
Thin FastAPI Agent Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from agent.application.commands.archive_agent import (
    ArchiveAgentCommand,
    ArchiveAgentHandler,
)
from agent.application.commands.clone_agent import (
    CloneAgentCommand,
    CloneAgentHandler,
)
from agent.application.commands.create_agent import (
    CreateAgentCommand,
    CreateAgentHandler,
)
from agent.application.commands.publish_agent import (
    PublishAgentCommand,
    PublishAgentHandler,
)
from agent.application.commands.update_agent import (
    UpdateAgentCommand,
    UpdateAgentHandler,
)
from agent.application.dto.agent_dto import AgentDTO
from agent.application.queries.get_agent import GetAgentHandler, GetAgentQuery
from agent.application.queries.list_agents import (
    ListAgentsHandler,
    ListAgentsQuery,
)
from agent.presentation.schemas.requests import (
    CloneAgentRequest,
    CreateAgentRequest,
    UpdateAgentRequest,
)
from agent.presentation.schemas.responses import (
    AgentLLMConfigResponse,
    AgentMemoryConfigResponse,
    AgentPolicyResponse,
    AgentResponse,
    AgentRuntimeConfigResponse,
    AgentToolResponse,
    AgentVoiceConfigResponse,
)

router = APIRouter(prefix="/agents", tags=["Agent Management"])


def _to_http_exception(error: Error) -> HTTPException:
    """Map domain Error to FastAPI HTTPException."""
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "PRECONDITION_FAILED": status.HTTP_412_PRECONDITION_FAILED,
        "INVALID_STATE": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": error.code, "message": error.message, "details": error.details},
    )


def _to_agent_response(dto: AgentDTO) -> AgentResponse:
    return AgentResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        name=dto.name,
        type=dto.type,
        status=dto.status,
        voice_config=AgentVoiceConfigResponse(
            tts_provider=dto.voice_config.tts_provider,
            voice_id=dto.voice_config.voice_id,
            speed=dto.voice_config.speed,
            pitch=dto.voice_config.pitch,
            language=dto.voice_config.language,
        ),
        runtime_config=AgentRuntimeConfigResponse(
            max_concurrent_sessions=dto.runtime_config.max_concurrent_sessions,
            session_timeout_seconds=dto.runtime_config.session_timeout_seconds,
            silence_threshold_ms=dto.runtime_config.silence_threshold_ms,
            barge_in_enabled=dto.runtime_config.barge_in_enabled,
        ),
        llm_config=AgentLLMConfigResponse(
            provider=dto.llm_config.provider,
            model=dto.llm_config.model,
            temperature=dto.llm_config.temperature,
            max_tokens=dto.llm_config.max_tokens,
            context_window=dto.llm_config.context_window,
        ),
        memory_config=AgentMemoryConfigResponse(
            short_term_window_size=dto.memory_config.short_term_window_size,
            long_term_enabled=dto.memory_config.long_term_enabled,
            long_term_strategy=dto.memory_config.long_term_strategy,
        ),
        playbook_id=dto.playbook_id,
        prompt_id=dto.prompt_id,
        tools=[
            AgentToolResponse(
                id=t.id,
                name=t.name,
                tool_type=t.tool_type,
                schema=t.schema,  # type: ignore[call-arg]
                config=t.config,  # type: ignore[call-arg]
                enabled=t.enabled,
            )
            for t in dto.tools
        ],
        policies=[
            AgentPolicyResponse(
                id=p.id,
                policy_type=p.policy_type,
                rule=p.rule,
                violation_action=p.violation_action,
                enforced=p.enforced,
                priority=p.priority,
            )
            for p in dto.policies
        ],
        version=dto.version,
        created_at=dto.created_at,
    )


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Agent",
)
async def create_agent(
    request: CreateAgentRequest,
    handler: CreateAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching CreateAgentCommand."""
    command = CreateAgentCommand(
        workspace_id=request.workspace_id,
        name=request.name,
        agent_type=request.agent_type,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent details by ID",
)
async def get_agent(
    agent_id: str,
    handler: GetAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching GetAgentQuery."""
    query = GetAgentQuery(agent_id=agent_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Agent configurations",
)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    handler: UpdateAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching UpdateAgentCommand."""
    command = UpdateAgentCommand(
        agent_id=agent_id,
        name=request.name,
        playbook_id=request.playbook_id,
        prompt_id=request.prompt_id,
        tts_provider=request.tts_provider,
        voice_id=request.voice_id,
        language=request.language,
        llm_provider=request.llm_provider,
        llm_model=request.llm_model,
        temperature=request.temperature,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.post(
    "/{agent_id}/publish",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish Agent (enforces Playbook & Prompt readiness)",
)
async def publish_agent(
    agent_id: str,
    handler: PublishAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching PublishAgentCommand."""
    command = PublishAgentCommand(agent_id=agent_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.post(
    "/{agent_id}/archive",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive Agent",
)
async def archive_agent(
    agent_id: str,
    handler: ArchiveAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching ArchiveAgentCommand."""
    command = ArchiveAgentCommand(agent_id=agent_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.post(
    "/{agent_id}/clone",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone Agent",
)
async def clone_agent(
    agent_id: str,
    request: CloneAgentRequest,
    handler: CloneAgentHandler = Depends(),
) -> AgentResponse:
    """Endpoint dispatching CloneAgentCommand."""
    command = CloneAgentCommand(
        source_agent_id=agent_id,
        new_name=request.new_name,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return _to_agent_response(result.value)


@router.get(
    "/workspace/{workspace_id}",
    response_model=list[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Agents in a Workspace",
)
async def list_agents(
    workspace_id: str,
    handler: ListAgentsHandler = Depends(),
) -> list[AgentResponse]:
    """Endpoint dispatching ListAgentsQuery."""
    query = ListAgentsQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)

    return [_to_agent_response(a) for a in result.value]
