"""
Pydantic Response Schemas for Voice Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AudioFormatResponse(BaseModel):
    sample_rate: int
    channels: int
    encoding: str
    container: str


class VoiceSessionMetricsResponse(BaseModel):
    total_turns: int
    audio_duration_seconds: float
    average_latency_ms: float
    stt_latency_ms: float
    tts_latency_ms: float


class VoiceParticipantResponse(BaseModel):
    id: str
    role: str
    display_name: str
    phone_number: str


class AudioStreamResponse(BaseModel):
    id: str
    stream_type: str
    audio_format: AudioFormatResponse
    is_active: bool
    chunks_processed: int
    total_bytes_processed: int


class VoiceTurnResponse(BaseModel):
    id: str
    speaker_role: str
    turn_number: int
    transcript: str
    confidence: float
    agent_response_text: str
    audio_synthesized: bool
    is_completed: bool


class VoiceSessionResponse(BaseModel):
    """HTTP Response schema representing a VoiceSession aggregate."""

    id: str = Field(..., description="VoiceSession ID")
    workspace_id: str = Field(..., description="Workspace ID")
    agent_id: str = Field(..., description="Agent ID")
    conversation_id: str = Field(..., description="Conversation ID")
    status: str = Field(..., description="Status (IDLE, CONNECTING, ACTIVE, PAUSED, ENDED, FAILED)")
    stt_provider_name: str = Field(..., description="STT provider name")
    tts_provider_name: str = Field(..., description="TTS provider name")
    telephony_provider_name: str = Field(..., description="Telephony provider name")
    participants: list[VoiceParticipantResponse] = Field(default_factory=list)
    streams: list[AudioStreamResponse] = Field(default_factory=list)
    turns: list[VoiceTurnResponse] = Field(default_factory=list)
    metrics: VoiceSessionMetricsResponse | None = None
    error_message: str = Field(default="", description="Error message if failed")
    version: int = Field(..., description="Aggregate version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
