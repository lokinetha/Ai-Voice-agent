"""
Thin FastAPI Conversation Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from conversation.application.commands.add_message import (
    AddMessageCommand,
    AddMessageHandler,
)
from conversation.application.commands.end_conversation import (
    EndConversationCommand,
    EndConversationHandler,
)
from conversation.application.commands.pause_conversation import (
    PauseConversationCommand,
    PauseConversationHandler,
)
from conversation.application.commands.resume_conversation import (
    ResumeConversationCommand,
    ResumeConversationHandler,
)
from conversation.application.commands.start_conversation import (
    StartConversationCommand,
    StartConversationHandler,
)
from conversation.application.commands.summarize_conversation import (
    SummarizeConversationCommand,
    SummarizeConversationHandler,
)
from conversation.application.dto.conversation_dto import (
    ConversationDTO,
    MessageDTO,
)
from conversation.application.queries.get_conversation import (
    GetConversationHandler,
    GetConversationQuery,
)
from conversation.application.queries.get_conversation_messages import (
    GetConversationMessagesHandler,
    GetConversationMessagesQuery,
)
from conversation.application.queries.list_conversations import (
    ListConversationsHandler,
    ListConversationsQuery,
)
from conversation.application.queries.search_conversation import (
    SearchConversationHandler,
    SearchConversationQuery,
)
from conversation.presentation.schemas.requests import (
    AddMessageRequest,
    EndConversationRequest,
    PauseConversationRequest,
    SearchConversationRequest,
    StartConversationRequest,
    SummarizeConversationRequest,
)
from conversation.presentation.schemas.responses import (
    ConversationMetricsResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    MessageResponse,
    ParticipantResponse,
)

router = APIRouter(prefix="/conversations", tags=["Conversation Management"])


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


def _to_msg_response(dto: MessageDTO) -> MessageResponse:
    return MessageResponse(
        id=dto.id,
        participant_id=dto.participant_id,
        participant_role=dto.participant_role,
        content=dto.content,
        sequence_number=dto.sequence_number,
        metadata=dto.metadata,
        created_at=dto.created_at,
    )


def _to_conv_response(dto: ConversationDTO) -> ConversationResponse:
    metrics = None
    if dto.metrics is not None:
        metrics = ConversationMetricsResponse(
            duration_seconds=dto.metrics.duration_seconds,
            total_messages=dto.metrics.total_messages,
            agent_messages=dto.metrics.agent_messages,
            customer_messages=dto.metrics.customer_messages,
            turn_count=dto.metrics.turn_count,
        )

    summary = None
    if dto.summary is not None:
        summary = ConversationSummaryResponse(
            text=dto.summary.text,
            key_topics=list(dto.summary.key_topics),
            sentiment=dto.summary.sentiment,
            action_items=list(dto.summary.action_items),
        )

    participants = [
        ParticipantResponse(
            id=p.id,
            name=p.name,
            role=p.role,
            external_id=p.external_id,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in dto.participants
    ]

    messages = [_to_msg_response(m) for m in dto.messages]

    return ConversationResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        agent_id=dto.agent_id,
        channel=dto.channel,
        language=dto.language,
        status=dto.status,
        message_count=dto.message_count,
        participant_count=dto.participant_count,
        version=dto.version,
        created_at=dto.created_at,
        metrics=metrics,
        summary=summary,
        participants=participants,
        messages=messages,
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new Conversation",
)
async def start_conversation(
    request: StartConversationRequest,
    handler: StartConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching StartConversationCommand."""
    command = StartConversationCommand(
        workspace_id=request.workspace_id,
        agent_id=request.agent_id,
        channel=request.channel,
        participant_name=request.participant_name,
        customer_external_id=request.customer_external_id,
        language=request.language,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation details",
)
async def get_conversation(
    conversation_id: str,
    handler: GetConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching GetConversationQuery."""
    query = GetConversationQuery(conversation_id=conversation_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Message to Conversation",
)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    handler: AddMessageHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching AddMessageCommand."""
    command = AddMessageCommand(
        conversation_id=conversation_id,
        participant_id=request.participant_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Conversation Messages",
)
async def get_conversation_messages(
    conversation_id: str,
    handler: GetConversationMessagesHandler = Depends(),
) -> list[MessageResponse]:
    """Endpoint dispatching GetConversationMessagesQuery."""
    query = GetConversationMessagesQuery(conversation_id=conversation_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_msg_response(m) for m in result.value]


@router.post(
    "/{conversation_id}/pause",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause Conversation",
)
async def pause_conversation(
    conversation_id: str,
    request: PauseConversationRequest,
    handler: PauseConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching PauseConversationCommand."""
    command = PauseConversationCommand(
        conversation_id=conversation_id,
        reason=request.reason,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.post(
    "/{conversation_id}/resume",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume Conversation",
)
async def resume_conversation(
    conversation_id: str,
    handler: ResumeConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching ResumeConversationCommand."""
    command = ResumeConversationCommand(conversation_id=conversation_id)
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.post(
    "/{conversation_id}/end",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="End Conversation",
)
async def end_conversation(
    conversation_id: str,
    request: EndConversationRequest,
    handler: EndConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching EndConversationCommand."""
    command = EndConversationCommand(
        conversation_id=conversation_id,
        reason=request.reason,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.post(
    "/{conversation_id}/summarize",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Summarize Conversation",
)
async def summarize_conversation(
    conversation_id: str,
    request: SummarizeConversationRequest,
    handler: SummarizeConversationHandler = Depends(),
) -> ConversationResponse:
    """Endpoint dispatching SummarizeConversationCommand."""
    command = SummarizeConversationCommand(
        conversation_id=conversation_id,
        summary_text=request.summary_text,
        key_topics=tuple(request.key_topics),
        sentiment=request.sentiment,
        action_items=tuple(request.action_items),
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_conv_response(result.value)


@router.get(
    "",
    response_model=list[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Conversations by Workspace",
)
async def list_conversations(
    workspace_id: str,
    handler: ListConversationsHandler = Depends(),
) -> list[ConversationResponse]:
    """Endpoint dispatching ListConversationsQuery."""
    query = ListConversationsQuery(workspace_id=workspace_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_conv_response(c) for c in result.value]


@router.post(
    "/search",
    response_model=list[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="Search Conversations",
)
async def search_conversations(
    request: SearchConversationRequest,
    handler: SearchConversationHandler = Depends(),
) -> list[ConversationResponse]:
    """Endpoint dispatching SearchConversationQuery."""
    query = SearchConversationQuery(
        agent_id=request.agent_id,
        status=request.status,
    )
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return [_to_conv_response(c) for c in result.value]
