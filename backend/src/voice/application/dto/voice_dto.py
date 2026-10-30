"""
Voice Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AudioFormatDTO:
    """DTO for AudioFormat parameters."""

    sample_rate: int
    channels: int
    encoding: str
    container: str


@dataclass(frozen=True)
class VoiceSessionMetricsDTO:
    """DTO for VoiceSessionMetrics."""

    total_turns: int
    audio_duration_seconds: float
    average_latency_ms: float
    stt_latency_ms: float
    tts_latency_ms: float


@dataclass(frozen=True)
class VoiceParticipantDTO:
    """DTO for VoiceParticipant entity."""

    id: str
    role: str
    display_name: str
    phone_number: str


@dataclass(frozen=True)
class AudioStreamDTO:
    """DTO for AudioStream entity."""

    id: str
    stream_type: str
    audio_format: AudioFormatDTO
    is_active: bool
    chunks_processed: int
    total_bytes_processed: int


@dataclass(frozen=True)
class VoiceTurnDTO:
    """DTO for VoiceTurn entity."""

    id: str
    speaker_role: str
    turn_number: int
    transcript: str
    confidence: float
    agent_response_text: str
    audio_synthesized: bool
    is_completed: bool


@dataclass(frozen=True)
class VoiceSessionDTO:
    """DTO for VoiceSession aggregate root."""

    id: str
    workspace_id: str
    agent_id: str
    conversation_id: str
    status: str
    stt_provider_name: str
    tts_provider_name: str
    telephony_provider_name: str
    participants: tuple[VoiceParticipantDTO, ...] = field(default_factory=tuple)
    streams: tuple[AudioStreamDTO, ...] = field(default_factory=tuple)
    turns: tuple[VoiceTurnDTO, ...] = field(default_factory=tuple)
    metrics: VoiceSessionMetricsDTO | None = None
    error_message: str = ""
    version: int = 1
    created_at: datetime | None = None
