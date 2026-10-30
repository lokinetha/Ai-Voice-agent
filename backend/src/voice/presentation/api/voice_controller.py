"""
Thin FastAPI Voice Controller.

Translates HTTP requests into Commands/Queries, dispatches to handlers,
and translates Result outputs into HTTP responses. Zero business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from shared.kernel.result import Error

from voice.application.commands.end_voice_session import (
    EndVoiceSessionCommand,
    EndVoiceSessionHandler,
)
from voice.application.commands.generate_agent_response import (
    GenerateAgentResponseCommand,
    GenerateAgentResponseHandler,
)
from voice.application.commands.process_transcript import (
    ProcessTranscriptCommand,
    ProcessTranscriptHandler,
)
from voice.application.commands.start_voice_session import (
    StartVoiceSessionCommand,
    StartVoiceSessionHandler,
)
from voice.application.commands.synthesize_response import (
    SynthesizeResponseCommand,
    SynthesizeResponseHandler,
)
from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.queries.get_voice_session import (
    GetVoiceSessionHandler,
    GetVoiceSessionQuery,
)
from voice.application.queries.get_voice_session_metrics import (
    GetVoiceSessionMetricsHandler,
    GetVoiceSessionMetricsQuery,
)
from voice.presentation.schemas.requests import (
    EndVoiceSessionRequest,
    GenerateAgentResponseRequest,
    ProcessTranscriptRequest,
    StartVoiceSessionRequest,
    SynthesizeResponseRequest,
)
from voice.presentation.schemas.responses import (
    AudioFormatResponse,
    AudioStreamResponse,
    VoiceParticipantResponse,
    VoiceSessionMetricsResponse,
    VoiceSessionResponse,
    VoiceTurnResponse,
)

router = APIRouter(prefix="/voice", tags=["Voice Sessions"])


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


def _to_session_response(dto: VoiceSessionDTO) -> VoiceSessionResponse:
    metrics = None
    if dto.metrics is not None:
        metrics = VoiceSessionMetricsResponse(
            total_turns=dto.metrics.total_turns,
            audio_duration_seconds=dto.metrics.audio_duration_seconds,
            average_latency_ms=dto.metrics.average_latency_ms,
            stt_latency_ms=dto.metrics.stt_latency_ms,
            tts_latency_ms=dto.metrics.tts_latency_ms,
        )

    participants = [
        VoiceParticipantResponse(
            id=p.id,
            role=p.role,
            display_name=p.display_name,
            phone_number=p.phone_number,
        )
        for p in dto.participants
    ]

    streams = [
        AudioStreamResponse(
            id=s.id,
            stream_type=s.stream_type,
            audio_format=AudioFormatResponse(
                sample_rate=s.audio_format.sample_rate,
                channels=s.audio_format.channels,
                encoding=s.audio_format.encoding,
                container=s.audio_format.container,
            ),
            is_active=s.is_active,
            chunks_processed=s.chunks_processed,
            total_bytes_processed=s.total_bytes_processed,
        )
        for s in dto.streams
    ]

    turns = [
        VoiceTurnResponse(
            id=t.id,
            speaker_role=t.speaker_role,
            turn_number=t.turn_number,
            transcript=t.transcript,
            confidence=t.confidence,
            agent_response_text=t.agent_response_text,
            audio_synthesized=t.audio_synthesized,
            is_completed=t.is_completed,
        )
        for t in dto.turns
    ]

    return VoiceSessionResponse(
        id=dto.id,
        workspace_id=dto.workspace_id,
        agent_id=dto.agent_id,
        conversation_id=dto.conversation_id,
        status=dto.status,
        stt_provider_name=dto.stt_provider_name,
        tts_provider_name=dto.tts_provider_name,
        telephony_provider_name=dto.telephony_provider_name,
        participants=participants,
        streams=streams,
        turns=turns,
        metrics=metrics,
        error_message=dto.error_message,
        version=dto.version,
        created_at=dto.created_at,
    )


@router.post(
    "/sessions",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new VoiceSession",
)
async def start_voice_session(
    request: StartVoiceSessionRequest,
    handler: StartVoiceSessionHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching StartVoiceSessionCommand."""
    command = StartVoiceSessionCommand(
        workspace_id=request.workspace_id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id,
        stt_provider_name=request.stt_provider_name,
        tts_provider_name=request.tts_provider_name,
        telephony_provider_name=request.telephony_provider_name,
        sample_rate=request.sample_rate,
        channels=request.channels,
        encoding=request.encoding,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.post(
    "/sessions/{session_id}/transcript",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Process transcribed user speech",
)
async def process_transcript(
    session_id: str,
    request: ProcessTranscriptRequest,
    handler: ProcessTranscriptHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching ProcessTranscriptCommand."""
    command = ProcessTranscriptCommand(
        session_id=session_id,
        transcript=request.transcript,
        confidence=request.confidence,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.post(
    "/sessions/{session_id}/agent-response",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Agent text response",
)
async def generate_agent_response(
    session_id: str,
    request: GenerateAgentResponseRequest,
    handler: GenerateAgentResponseHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching GenerateAgentResponseCommand."""
    command = GenerateAgentResponseCommand(
        session_id=session_id,
        user_prompt=request.user_prompt,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.post(
    "/sessions/{session_id}/synthesize",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize agent response to audio",
)
async def synthesize_response(
    session_id: str,
    request: SynthesizeResponseRequest,
    handler: SynthesizeResponseHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching SynthesizeResponseCommand."""
    command = SynthesizeResponseCommand(
        session_id=session_id,
        voice_id=request.voice_id,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.post(
    "/sessions/{session_id}/end",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="End VoiceSession",
)
async def end_voice_session(
    session_id: str,
    request: EndVoiceSessionRequest,
    handler: EndVoiceSessionHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching EndVoiceSessionCommand."""
    command = EndVoiceSessionCommand(
        session_id=session_id,
        reason=request.reason,
    )
    result = await handler.handle(command)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.get(
    "/sessions/{session_id}",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VoiceSession details",
)
async def get_voice_session(
    session_id: str,
    handler: GetVoiceSessionHandler = Depends(),
) -> VoiceSessionResponse:
    """Endpoint dispatching GetVoiceSessionQuery."""
    query = GetVoiceSessionQuery(session_id=session_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return _to_session_response(result.value)


@router.get(
    "/sessions/{session_id}/metrics",
    response_model=VoiceSessionMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VoiceSession operational metrics",
)
async def get_voice_session_metrics(
    session_id: str,
    handler: GetVoiceSessionMetricsHandler = Depends(),
) -> VoiceSessionMetricsResponse:
    """Endpoint dispatching GetVoiceSessionMetricsQuery."""
    query = GetVoiceSessionMetricsQuery(session_id=session_id)
    result = await handler.handle(query)
    if result.is_failure:
        raise _to_http_exception(result.error)
    return VoiceSessionMetricsResponse(
        total_turns=result.value.total_turns,
        audio_duration_seconds=result.value.audio_duration_seconds,
        average_latency_ms=result.value.average_latency_ms,
        stt_latency_ms=result.value.stt_latency_ms,
        tts_latency_ms=result.value.tts_latency_ms,
    )
